# SPDX-License-Identifier: NOASSERTION
# Copyright (c) 2025 Shahin

"""Voice I/O module for Sofware-AI.

This module handles speech-to-text and text-to-speech functionality.
"""

import os
import queue
import threading
import logging
import tempfile
import subprocess
from typing import Optional, Callable, Any, cast, Literal
import speech_recognition as sr
from google.cloud import texttospeech
from gtts import gTTS
import sounddevice as sd
import soundfile as sf
from pydub import AudioSegment
import io

logger = logging.getLogger(__name__)

class VoiceInput:
    """Manages voice input (speech-to-text)."""
    def __init__(self) -> None:
        """Initialize speech recognizer and microphone."""
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.stop_listening: Optional[Callable[[], None]] = None
        self.audio_queue = queue.Queue()
        self.listening_thread: Optional[threading.Thread] = None
        self.is_listening = False
        self._setup_recognition()

    def _setup_recognition(self) -> None:
        """Configure speech recognizer and reduce ambient noise."""
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
            # Set speech recognition sensitivity
            self.recognizer.energy_threshold = 4000
            self.recognizer.dynamic_energy_threshold = True

    def listen_once(self, timeout: Optional[int] = None) -> str:
        """Listen once and convert speech to text.
        
        Args:
            timeout: timeout in seconds (None for unlimited)
            
        Returns:
            recognized text or empty string on error
        """
        try:
            with self.microphone as source:
                logger.info("Listening for speech...")
                audio = self.recognizer.listen(source, timeout=timeout)

            text = cast(Any, self.recognizer).recognize_google(audio, language="fa-IR")
            logger.info(f"Recognized speech: {text}")
            return text
        except sr.WaitTimeoutError:
            logger.warning("Listen timed out.")
            return ""
        except sr.UnknownValueError:
            logger.error("Could not understand audio.")
            return ""
        except sr.RequestError as e:
            logger.error(f"Speech recognition service error: {str(e)}")
            return ""
        except Exception as e:
            logger.error(f"Unexpected error during listening: {str(e)}")
            
        return ""
        
    def start_continuous(self, callback: Callable[[str], Any]) -> None:
        """Start continuous listening in a background thread.
        
        Args:
            callback: function called with recognized text
        """
        def listener_thread():
            while self.is_listening:
                text = self.listen_once()
                if text:
                    callback(text)

        self.is_listening = True
        threading.Thread(target=listener_thread, daemon=True).start()

    def stop_continuous(self) -> None:
        """Stop continuous listening."""
        self.is_listening = False

class VoiceOutput:
    """Manages text-to-speech output.

    Supports two TTS providers:
    - Google Cloud TTS (google-cloud): higher quality, paid
    - gTTS (gtts): free, reasonable quality
    """
    
    def __init__(self, tts_provider: Literal["google-cloud", "gtts"] = "google-cloud") -> None:
        """Initialize the TTS engine.
        
        Args:
            tts_provider: which TTS backend to use
                - "google-cloud": Google Cloud Text-to-Speech (requires credentials)
                - "gtts": gTTS (free)
        """
        self.tts_provider = tts_provider
        self.speaking_queue = queue.Queue()
        self.is_speaking = False
        self.temp_dir = tempfile.mkdtemp()
        
        # Initialize Google Cloud service (if used)
        if self.tts_provider == "google-cloud":
            self.client = texttospeech.TextToSpeechClient()
            self.voice = texttospeech.VoiceSelectionParams(
                language_code="fa-IR",
                name="fa-IR-Standard-A"
            )
            self.audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.LINEAR16,
                speaking_rate=1.0,
                pitch=0.0,
                volume_gain_db=0.0
            )
            logger.info("TTS Provider: Google Cloud Text-to-Speech")
        else:
            logger.info("TTS Provider: gTTS (free)")
        
        self._start_speaker_thread()

    def _synthesize_speech_google_cloud(self, text: str) -> bytes:
        """Synthesize speech using Google Cloud TTS.
        
        Args:
            text: text to synthesize
            
        Returns:
            raw audio bytes
        """
        synthesis_input = texttospeech.SynthesisInput(text=text)
        response = self.client.synthesize_speech(
            input=synthesis_input,
            voice=self.voice,
            audio_config=self.audio_config
        )
        return response.audio_content

    def _synthesize_speech_gtts(self, text: str) -> bytes:
        """Synthesize speech using gTTS.
        
        Args:
            text: text to synthesize
            
        Returns:
            raw audio bytes
        """
        temp_mp3 = os.path.join(self.temp_dir, "temp_gtts.mp3")
        try:
            # Create and save gTTS audio file
            # Note: gTTS does not support Persian reliably, so output is in English
            tts = gTTS(text=text, lang='en', slow=False)
            tts.save(temp_mp3)

            # Read MP3 file and return bytes
            with open(temp_mp3, 'rb') as f:
                audio_bytes = f.read()

            return audio_bytes
        finally:
            # Clean up temporary file
            if os.path.exists(temp_mp3):
                os.remove(temp_mp3)

    def _synthesize_speech(self, text: str) -> bytes:
        """Synthesize speech using the selected provider.
        
        Args:
            text: text to synthesize
            
        Returns:
            raw audio bytes
        """
        if self.tts_provider == "google-cloud":
            return self._synthesize_speech_google_cloud(text)
        else:
            return self._synthesize_speech_gtts(text)

    def _play_audio(self, audio_content: bytes, is_mp3: bool = False) -> None:
        """Play audio using sounddevice and ffplay.
        
        Args:
            audio_content: raw audio bytes
            is_mp3: whether the content is MP3 (used by gTTS)
        """
        if is_mp3:
            # For gTTS which returns MP3
            temp_mp3 = os.path.join(self.temp_dir, "temp_audio.mp3")
            try:
                # Save MP3
                with open(temp_mp3, 'wb') as f:
                    f.write(audio_content)
                
                # Try to play MP3 with ffplay
                try:
                    import subprocess
                    subprocess.run(["ffplay", "-nodisp", "-autoexit", temp_mp3], 
                                 check=True, 
                                 stdout=subprocess.DEVNULL, 
                                 stderr=subprocess.DEVNULL,
                                 timeout=30)
                except Exception as play_error:
                    logger.warning(f"ffplay not available or failed:\n{str(play_error)}")
                    logger.info("To play audio correctly, install ffmpeg: choco install ffmpeg")
            finally:
                if os.path.exists(temp_mp3):
                    os.remove(temp_mp3)
        else:
            # For Google Cloud which returns WAV
            temp_wav = os.path.join(self.temp_dir, "temp_speech.wav")
            with open(temp_wav, "wb") as f:
                f.write(audio_content)
            
            try:
                data, samplerate = sf.read(temp_wav)
                sd.play(data, samplerate)
                sd.wait()
            finally:
                if os.path.exists(temp_wav):
                    os.remove(temp_wav)

    def _start_speaker_thread(self) -> None:
        """Start the background thread that manages the speaking queue."""
        def speaker_thread():
            while True:
                try:
                    text = self.speaking_queue.get()
                    if text is None:  # stop signal
                        break
                    
                    self.is_speaking = True
                    audio_content = self._synthesize_speech(text)
                    
                    # Determine audio format based on provider
                    is_mp3 = self.tts_provider == "gtts"
                    self._play_audio(audio_content, is_mp3=is_mp3)
                except Exception as e:
                    logger.error(f"Error playing speech:\n{str(e)}")
                finally:
                    self.is_speaking = False
                    self.speaking_queue.task_done()
        
        self.speaker_thread = threading.Thread(target=speaker_thread, daemon=True)
        self.speaker_thread.start()

    def speak(self, text: str, block: bool = False) -> None:
        """Enqueue text to be spoken.
        
        Args:
            text: text to speak
            block: if True, wait until speaking finishes
        """
        try:
            self.speaking_queue.put(text)
            if block:
                self.speaking_queue.join()
        except Exception as e:
            logger.error(f"Error adding text to speaking queue: {str(e)}")

    def stop_speaking(self) -> None:
        """Immediately stop current speech and clear the queue."""
        with self.speaking_queue.mutex:
            self.speaking_queue.queue.clear()

    def shutdown(self) -> None:
        """Shut down the TTS engine."""
        try:
            self.speaking_queue.put(None)  # send stop signal
            self.speaker_thread.join()
            if os.path.exists(self.temp_dir):
                os.rmdir(self.temp_dir)
        except Exception as e:
            logger.error(f"Error shutting down TTS engine: {str(e)}")

class VoiceManager:
    """Unified manager for voice input and output."""

    def __init__(self, tts_provider: Literal["google-cloud", "gtts"] = "google-cloud") -> None:
        """Initialize the voice manager.
        
        Args:
            tts_provider: which TTS backend to use
                - "google-cloud": Google Cloud Text-to-Speech
                - "gtts": gTTS (free)
        """
        self.voice_input = VoiceInput()
        self.voice_output = VoiceOutput(tts_provider=tts_provider)

    def listen(self, timeout: Optional[int] = None) -> str:
        """Perform a single listen on voice input.
        
        Args:
            timeout: timeout in seconds
            
        Returns:
            recognized text
        """
        return self.voice_input.listen_once(timeout)
    
    def speak(self, text: str, block: bool = False) -> None:
        """Convert text to speech and speak it.
        Args:
            text: text to speak
            block: if True, wait until speaking finishes
        """
        self.voice_output.speak(text, block)

    def start_conversation(self, callback: Callable[[str], Any]) -> None:
        """Start two-way conversation (continuous listen with callback).
        
        Args:
            callback: function called with recognized text
        """
        self.voice_input.start_continuous(callback)

    def stop_conversation(self) -> None:
        """Stop two-way conversation."""
        self.voice_input.stop_continuous()
        self.voice_output.stop_speaking()

    def shutdown(self) -> None:
        """Cleanly shut down the voice system."""
        self.stop_conversation()
        self.voice_output.shutdown()