# SPDX-License-Identifier: NOASSERTION
# Copyright (c) 2025 Shahin

"""
ماژول ورودی/خروجی صوتی برای Sofware-AI
این ماژول مسئول تبدیل گفتار به متن و متن به گفتار است.
"""

import queue
import threading
import logging
from typing import Optional, Callable, Any, cast
import speech_recognition as sr
import pyttsx3
import collections.abc

logger = logging.getLogger(__name__)

class VoiceInput: 
    """کلاس مدیریت ورودی صوتی (تبدیل گفتار به متن)"""
    def __init__(self) -> None:
        """مقداردهی اولیه تشخیص گفتار"""
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.stop_listening: Optional[Callable[[], None]] = None
        self.audio_queue = queue.Queue()
        self.listening_thread: Optional[threading.Thread] = None
        self.is_listening = False
        self._setup_recognition()

    def _setup_recognition(self) -> None:
        """تنظیم پارامترهای تشخیص صدا و حذف نویز محیط"""
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
            # تنظیم حساسیت تشخیص صدا
            self.recognizer.energy_threshold = 4000
            self.recognizer.dynamic_energy_threshold = True

    def listen_once(self, timeout: Optional[int] = None) -> str:
        """یک‌بار گوش دادن و تبدیل گفتار به متن
        
        Args:
            timeout: زمان انتظار به ثانیه (None برای نامحدود)
            
        Returns:
            متن تشخیص داده شده یا رشته خالی در صورت خطا
        """
        try:
            with self.microphone as source:
                logger.info("Dar hale Goosh dadan...")
                audio = self.recognizer.listen(source, timeout=timeout)

            text = cast(Any, self.recognizer).recognize_google(audio, language="fa-IR")
            logger.info(f"Tashkhis Dade Shod: {text}")
            return text
        except sr.WaitTimeoutError:
            logger.warning("Zaman-e entezaar be payan resid.")
            return ""
        except sr.UnknownValueError:
            logger.error("Gofte shode ra nemitavan tashkhis dad.")
            return ""
        except sr.RequestError as e:
            logger.error(f"Khataye khadamat-e tashkhis: {str(e)}")
            return ""
        except Exception as e:
            logger.error(f"Khataye gheire montazere: {str(e)}")
            
        return ""
        
    def start_continuous(self, callback: Callable[[str], Any]) -> None:
        """شروع گوش دادن مداوم در یک thread جداگانه
        
        Args:
            callback: تابعی که با متن تشخیص داده شده فراخوانی می‌شود
        """
        def listener_thread():
            while self.is_listening:
                text = self.listen_once()
                if text:
                    callback(text)

        self.is_listening = True
        threading.Thread(target=listener_thread, daemon=True).start()

    def stop_continuous(self) -> None:
        """توقف گوش دادن مداوم"""
        self.is_listening = False

class VoiceOutput:
    """کلاس مدیریت خروجی صوتی (تبدیل متن به گفتار)"""
    def __init__(self) -> None:
        """مقداردهی اولیه موتور تبدیل متن به گفتار"""
        self.engine = pyttsx3.init()
        self._setup_engine()
        self.speaking_queue = queue.Queue()
        self.is_speaking = False
        self._start_speaker_thread()

    def _setup_engine(self) -> None:
        """تنظیم پارامترهای موتور تبدیل متن به گفتار"""
        # تنظیم سرعت (کلمات در دقیقه)
        self.engine.setProperty('rate', 150)
        # تنظیم بلندی صدا (0 تا 1)
        self.engine.setProperty('volume', 0.9)

        # انتخاب صدای فارسی اگر موجود باشد
        voices = self.engine.getProperty('voices')
        # اطمینان حاصل کنید که صداها قابل تکرار هستند - برخی از backendها ممکن است یک شیء غیرقابل تکرار را برگردانند
        if isinstance(voices, collections.abc.Iterable):
            iterable_voices = list(voices)
        else:
            # تلاش برای شکل‌های رایج جایگزین، در غیر این صورت استفاده از لیست خالی
            fallback = getattr(voices, 'voices', None) or getattr(voices, '_voices', None) or []
            if isinstance(fallback, collections.abc.Iterable):
                iterable_voices = list(fallback)
            else:
                iterable_voices = []

        for voice in iterable_voices:
            try:
                langs = []
                if hasattr(voice, 'languages'):
                    langs = voice.languages
                elif hasattr(voice, 'id') and isinstance(voice.id, str):
                    langs = [voice.id]
                name = getattr(voice, 'name', '') or ''
                if any('fa' in str(l).lower() for l in langs) or 'persian' in name.lower():
                    self.engine.setProperty('voice', voice.id)
                    break
            except Exception:
                # از اشیاء صوتی که ویژگی‌های مورد انتظار را ندارند، صرف نظر کنید
                continue
    def _start_speaker_thread(self) -> None:
        """راه‌اندازی thread مدیریت صف گفتار"""
        def speaker_thread():
            while True:
                try:
                    text = self.speaking_queue.get()
                    if text is None: # سیگنال توقف
                        break
                    self.is_speaking = True
                    self.engine.say(text)
                    self.engine.runAndWait()
                except Exception as e:
                    logger.error(f"khata dar pokhsh goftar: {str(e)}")
                finally:
                    self.is_speaking = False
                    self.speaking_queue.task_done()
        self.speaker_thread = threading.Thread(target=speaker_thread, daemon=True)
        self.speaker_thread.start()

    def speak(self, text: str, block: bool = False) -> None:
        """تبدیل متن به گفتار
        
        Args:
            text: متن برای تبدیل به گفتار
            block: اگر True باشد، منتظر اتمام گفتار می‌ماند
        """
        try:
            self.speaking_queue.put(text)
            if block:
                self.speaking_queue.join()
        except Exception as e:
            logger.error(f"khata dar afzodane matn be safhe goftar: {str(e)}")

    def stop_speaking(self) -> None:
        """توقف فوری گفتار فعلی و پاک‌سازی صف"""
        try:
            self.engine.stop()
            with self.speaking_queue.mutex:
                self.speaking_queue.queue.clear()
        except Exception as e:
            logger.error(f"Khataye dar tavaghof goftar: {str(e)}")

    def shutdown(self) -> None:
        """خاموش کردن موتور تبدیل متن به گفتار"""
        try:
            self.speaking_queue.put(None)  # ارسال سیگنال توقف
            self.speaker_thread.join()
            self.engine.stop()
        except Exception as e:
            logger.error(f"Khataye dar khamosh shodan motor: {str(e)}")

class VoiceManager:
    """مدیریت یکپارچه ورودی و خروجی صوتی"""

    def __init__(self) -> None:
        """مقداردهی اولیه مدیر صوتی"""
        self.voice_input = VoiceInput()
        self.voice_output = VoiceOutput()

    def listen(self, timeout: Optional[int] = None) -> str:
        """گوش دادن یک‌باره به ورودی صوتی
        
        Args:
            timeout: زمان انتظار به ثانیه
            
        Returns:
            متن تشخیص داده شده
        """
        return self.voice_input.listen_once(timeout)
    
    def speak(self, text: str, block: bool = False) -> None:
        """تبدیل متن به گفتار
        Args:
            text: متن برای تبدیل به گفتار
            block: اگر True باشد، منتظر اتمام گفتار می‌ماند
        """
        self.voice_output.speak(text, block)

    def start_conversation(self, callback: Callable[[str], Any]) -> None:
        """شروع مکالمه دوطرفه
        
        Args:
            callback: تابعی که با متن تشخیص داده شده فراخوانی می‌شود
        """
        self.voice_input.start_continuous(callback)

    def stop_conversation(self) -> None:
        """توقف مکالمه دوطرفه"""
        self.voice_input.stop_continuous()
        self.voice_output.stop_speaking()

    def shutdown(self) -> None:
        """بستن تمیز سیستم صوتی"""
        self.stop_conversation()
        self.voice_output.shutdown()