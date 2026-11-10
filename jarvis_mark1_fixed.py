import pyttsx3
import datetime
import webbrowser
import tkinter as tk
from tkinter.scrolledtext import ScrolledText
import threading
import speech_recognition as sr
import sys
import wikipedia
import queue

# ------------------ Voice Engine Setup ------------------ #
speech_queue = queue.Queue()

def tts_worker():
    # NOTE: pyttsx3's SAPI5 backend on Windows has a well-known bug where a
    # single reused engine instance will speak the first queued item fine and
    # then silently stop producing audio for everything after it. The fix is
    # to create (and dispose of) a fresh engine for every utterance instead
    # of reusing one instance across the whole program's lifetime.
    while True:
        text = speech_queue.get()
        if text is None:
            speech_queue.task_done()
            break
        try:
            engine = pyttsx3.init('sapi5')
            voices = engine.getProperty('voices')
            engine.setProperty('voice', voices[0].id)
            engine.setProperty('rate', 190)
            engine.say(text)
            engine.runAndWait()
            engine.stop()
            del engine
        except Exception as e:
            print(f"[TTS error: {e}]")
        speech_queue.task_done()

threading.Thread(target=tts_worker, daemon=True).start()

def speak(audio):
    speech_queue.put(audio)

def say(text):
    """Print to the GUI and speak, exactly once each, in that order."""
    print(text)
    speak(text)

# ------------------ GUI Setup ------------------ #
root = tk.Tk()
root.title("Jarvis - Console Output")
root.geometry("600x400")

output_box = ScrolledText(root, wrap=tk.WORD, font=("Arial", 16, "bold"), bg="#1e1e1e", fg="#d4d4d4", insertbackground="white")
output_box.pack(expand=True, fill='both')

entry_frame = tk.Frame(root, bg="#1e1e1e")
entry_frame.pack(fill='x')

entry = tk.Text(entry_frame, height=3, font=("Courier", 16), bg="#1e1e1e", fg="white", insertbackground="white")
entry.pack(side='left', expand=True, fill='both', padx=5, pady=5)

def gui_print(text):
    def _insert():
        output_box.insert(tk.END, text + '\n')
        output_box.see(tk.END)
    output_box.after(0, _insert)

class StdoutRedirector:
    def __init__(self, widget):
        self.widget = widget
        
    def write(self, message):
        # Update GUI console box only. Speech is triggered explicitly via
        # say()/speak() so each message is queued exactly once — previously
        # this also called speak() on every print(), which double-queued
        # text (since callers already called speak() themselves) and made
        # the "engine goes stale after one utterance" bug worse.
        self.widget.after(0, self._insert_text, message)
        
    def _insert_text(self, message):
        self.widget.insert(tk.END, message)
        self.widget.see(tk.END)
        
    def flush(self):
        pass

sys.stdout = StdoutRedirector(output_box)

# ------------------ Wikipedia Search Function ------------------ #
wikipedia.set_lang("en")

def wiki_search(query):
    try:
        for prefix in ["what is", "who is", "define"]:
            if query.startswith(prefix):
                topic = query[len(prefix):].strip()
                break
        else:
            topic = query.strip()

        results = wikipedia.search(topic)
        if not results:
            return f"No relevant Wikipedia page found for '{topic}'."

        summary = wikipedia.summary(results[0], sentences=3)
        return summary

    except wikipedia.exceptions.DisambiguationError as e:
        options = "\n".join(e.options[:5])
        return f"'{topic}' may refer to multiple topics. Please be more specific:\n{options}"

    except wikipedia.exceptions.PageError:
        return f"No page found for '{topic}'."

    except Exception as e:
        return f"An error occurred: {e}"

# ------------------ Main Functions ------------------ #
def wishme():
    hour = int(datetime.datetime.now().hour)
    if hour >= 0 and hour < 12:
        say('Good morning sir')
    elif hour >= 12 and hour < 18:
        say('Good afternoon sir')
    else:
        say('Good evening sir')

    say('I am JARVIS personal voice assistant')
    say('How may I help you sir')

def handle_input(query):
    query = query.lower()

    if 'open youtube' in query:
        say('Opening YouTube sir')
        webbrowser.open('https://www.youtube.com')

    elif 'open google' in query:
        webbrowser.open('https://www.google.com')
        say('Opening Google sir')

    elif 'how are you' in query:
        say('I am fine sir')

    elif 'who are you' in query:
        say('I am Jarvis, your personal voice assistant')

    elif 'the time' in query:
        time = datetime.datetime.now().strftime("%H:%M")
        say(f'Sir, the time is {time}')

    elif 'reboot' in query:
        say('I am rebooting myself sir')
        say('Reboot complete')

    elif 'quit' in query:
        say('Quitting sir')
        return False

    elif 'shutdown' in query:
        say('Shutting down sir')
        root.quit()

    elif 'what is' in query or 'who is' in query or 'define' in query:
        result = wiki_search(query)
        say('Here is what I found')
        say(result)

    else:
        say('Sorry sir, I did not understand')

    return True

def process_text_input():
    text = entry.get("1.0", tk.END).strip()
    if text:
        print(f'You typed: {text}')
        entry.delete("1.0", tk.END)
        keep_running = handle_input(text)
        if not keep_running:
            root.quit()

entry_button = tk.Button(entry_frame, text="Send", font=("Arial", 10, "bold"), command=process_text_input, width=10, height=2, bg="white", fg="blue")
entry_button.pack(side='right', padx=5)

def take_voice_command():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening for 'Jarvis' ...")
        r.pause_threshold = 1
        audio = r.listen(source)

    try:
        command = r.recognize_google(audio)
        print(f"You said: {command}")
        return command
    except Exception as e:
        print(f"Error: {e}")
        return ""

def run_jarvis():
    wishme()
    while True:
        voice_input = take_voice_command().lower()
        if 'jarvis' in voice_input:
            say('I am on, how may I help sir!')
            while True:
                command = take_voice_command()
                if not handle_input(command):
                    return

# ------------------ Run GUI + Jarvis ------------------ #
if __name__ == "__main__":
    jarvis_thread = threading.Thread(target=run_jarvis)
    jarvis_thread.start()
    root.mainloop()