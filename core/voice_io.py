# SPDX-License-Identifier: NOASSERTION
# Copyright (c) 2025 Shahin

"""
Voice Input/Output module for Sofware-AI
This module is responsible for speech-to-text and text-to-speech conversion.
"""

import os
import queue
import threading
import logging
import tempfile
from typing import Optional, Callable, Any, cast
import speech_recognition as sr
from google.cloud import texttospeech
import sounddevice as sd
import soundfile as sf

logger = logging.getLogger(__name__)

class VoiceInput: 
    """Voice Input Management Class (Speech-to-Text conversion)"""
    def __init__(self) -> None:
        """Initialize speech recognition"""
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.stop_listening: Optional[Callable[[], None]] = None
        self.audio_queue = queue.Queue()
        self.listening_thread: Optional[threading.Thread] = None
        self.is_listening = False
        self._setup_recognition()

    def _setup_recognition(self) -> None:
        """Set up voice recognition parameters and remove ambient noise"""
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
            # Set voice detection sensitivity
            self.recognizer.energy_threshold = 4000
            self.recognizer.dynamic_energy_threshold = True

    def listen_once(self, timeout: Optional[int] = None) -> str:
        """Listen once and convert speech to text
        
        Args:
            timeout: Wait time in seconds (None for unlimited)
            
        Returns:
            Recognized text or empty string in case of error
        """
        try:
            with self.microphone as source:
                logger.info("Listening...")
                audio = self.recognizer.listen(source, timeout=timeout)

            text = cast(Any, self.recognizer).recognize_google(audio, language="fa-IR")
            logger.info(f"Recognized: {text}")
            return text
        except sr.WaitTimeoutError:
            logger.warning("Wait time has expired.")
            return ""
        except sr.UnknownValueError:
            logger.error("Could not recognize the speech.")
            return ""
        except sr.RequestError as e:
            logger.error(f"Recognition service error: {str(e)}")
            return ""
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            
        return ""
        
    def start_continuous(self, callback: Callable[[str], Any]) -> None:
        """Start continuous listening in a separate thread
        
        Args:
            callback: Function to be called with the recognized text
        """
        def listener_thread():
            while self.is_listening:
                text = self.listen_once()
                if text:
                    callback(text)

        self.is_listening = True
        threading.Thread(target=listener_thread, daemon=True).start()

    def stop_continuous(self) -> None:
        """Stop continuous listening"""
        self.is_listening = False

class VoiceOutput:
    """Voice Output Management Class (Text-to-Speech using Google Cloud)"""
    def __init__(self) -> None:
        """Initialize text-to-speech engine"""
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
        self.speaking_queue = queue.Queue()
        self.is_speaking = False
        self.temp_dir = tempfile.mkdtemp()
        self._start_speaker_thread()

    def _synthesize_speech(self, text: str) -> bytes:
        """Synthesize speech using Google Cloud TTS.

        Args:
            text: The text to convert to speech

        Returns:
            Audio data as bytes
        """
        synthesis_input = texttospeech.SynthesisInput(text=text)
        response = self.client.synthesize_speech(
            input=synthesis_input,
            voice=self.voice,
            audio_config=self.audio_config
        )
        return response.audio_content

    def _play_audio(self, audio_content: bytes) -> None:
        """Play audio using sounddevice.

        Args:
            audio_content: Audio data as bytes
        """
        temp_file = os.path.join(self.temp_dir, "temp_speech.wav")
        with open(temp_file, "wb") as f:
            f.write(audio_content)
        
        data, samplerate = sf.read(temp_file)
        sd.play(data, samplerate)
        sd.wait()
        os.remove(temp_file)
    def _start_speaker_thread(self) -> None:
        """Start the speaker queue management thread"""
        def speaker_thread():
            while True:
                try:
                    text = self.speaking_queue.get()
                    if text is None:  # stop signal
                        break
                    self.is_speaking = True
                    audio_content = self._synthesize_speech(text)
                    self._play_audio(audio_content)
                except Exception as e:
                    logger.error(f"Error while playing speech: {str(e)}")
                finally:
                    self.is_speaking = False
                    self.speaking_queue.task_done()
        
        self.speaker_thread = threading.Thread(target=speaker_thread, daemon=True)
        self.speaker_thread.start()

    def speak(self, text: str, block: bool = False) -> None:
        """Convert text to speech.

        Args:
            text: The text to convert to speech
            block: If True, wait for the speech to finish
        """
        try:
            self.speaking_queue.put(text)
            if block:
                self.speaking_queue.join()
        except Exception as e:
            logger.error(f"Error adding text to speech queue: {str(e)}")

    def stop_speaking(self) -> None:
        """Immediately stop current speech and clear the queue"""
        with self.speaking_queue.mutex:
            self.speaking_queue.queue.clear()

    def shutdown(self) -> None:
        """Shutdown the text-to-speech engine"""
        try:
            self.speaking_queue.put(None)  # send stop signal
            self.speaker_thread.join()
            if os.path.exists(self.temp_dir):
                os.rmdir(self.temp_dir)
        except Exception as e:
            logger.error(f"Error while shutting down TTS engine: {str(e)}")

class VoiceManager:
    """Unified manager for voice input and output"""

    def __init__(self) -> None:
        """Initialize the voice manager"""
        self.voice_input = VoiceInput()
        self.voice_output = VoiceOutput()

    def listen(self, timeout: Optional[int] = None) -> str:
        """Listen once to voice input.

        Args:
            timeout: Wait time in seconds

        Returns:
            Recognized text
        """
        return self.voice_input.listen_once(timeout)
    
    def speak(self, text: str, block: bool = False) -> None:
        """Convert text to speech.

        Args:
            text: The text to convert to speech
            block: If True, wait for the speech to finish
        """
        self.voice_output.speak(text, block)

    def start_conversation(self, callback: Callable[[str], Any]) -> None:
        """Start a two-way conversation.

        Args:
            callback: Function that will be called with the recognized text
        """
        self.voice_input.start_continuous(callback)

    def stop_conversation(self) -> None:
        """Stop the two-way conversation"""
        self.voice_input.stop_continuous()
        self.voice_output.stop_speaking()

    def shutdown(self) -> None:
        """Cleanly shutdown the voice system"""
        self.stop_conversation()
        self.voice_output.shutdown()