import tkinter as tk
from tkinter import ttk, messagebox
from ttkbootstrap import Style
import json
import time
import pickle
import os.path
import tzlocal 
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import datetime


SCOPES = ['https://www.googleapis.com/auth/calendar.events']


class TodoListApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("DoItWithCal")
        self.geometry("400x400")
        style = Style(theme="flatly")
        style.configure("Custon.TEntry", foreground="gray")

        self.task_input = ttk.Entry(self, font=(
            "TkDefaultFont", 16), width=30, style="Custon.TEntry")
        self.task_input.pack(pady=10)

        self.task_input.insert(0, "Enter your todo here...")

        self.task_input.bind("<FocusIn>", self.clear_placeholder)
        self.task_input.bind("<FocusOut>", self.restore_placeholder)

        self.pending_tasks = {}

        self.set_service(self.connect())

        self.pending = False

        ttk.Button(self, text="Add", command=self.add_task).pack(pady=5)

        self.task_list = tk.Listbox(self, font=(
            "TkDefaultFont", 16), height=10, selectmode=tk.NONE)
        self.task_list.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)


        ttk.Button(self, text="Done", style="success.TButton",
                   command=self.mark_done).pack(side=tk.LEFT, padx=1, pady=1)
        ttk.Button(self, text="Delete", style="danger.TButton",
                   command=self.delete_task).pack(side=tk.RIGHT, padx=1, pady=1)
        
        ttk.Button(self, text="Pending", style="info.TButton",
                   command=self.mark_pending).pack(side=tk.BOTTOM, pady=1)
        
        self.load_tasks()
    

    def set_service(self, service):
        self.service = service


    def view_stats(self):
        done_count = 0
        total_count = self.task_list.size()
        for i in range(total_count):
            if self.task_list.itemcget(i, "fg") == "green":
                done_count += 1
        messagebox.showinfo("Task Statistics", f"Total tasks: {total_count}\nCompleted tasks: {done_count}")

    def add_task(self):
        task = self.task_input.get()
        if task != "Enter your todo here...":
            self.task_list.insert(tk.END, task)
            self.task_list.itemconfig(tk.END, fg="orange")
            self.task_input.delete(0, tk.END)
            self.save_tasks()


    def mark_pending(self):
        if self.pending:
            messagebox.showinfo("Not So Fast!","Finsh Your previous Pending Task Champ!")
            return 0
        task_index = self.task_list.curselection()
        if task_index:
            self.task_list.itemconfig(task_index, fg="blue")
            task_text = self.task_list.get(task_index)
            self.pending_tasks[task_text] = datetime.datetime.now()
            self.pending = True  
            self.save_tasks()
            



    def mark_done(self):
        task_index = self.task_list.curselection()
        if task_index:
            self.task_list.itemconfig(task_index, fg="green")
            task_text = self.task_list.get(task_index)

            if task_text in self.pending_tasks:
                start_time = self.pending_tasks[task_text]
                end_time = datetime.datetime.now()

                duration = end_time - start_time

                self.create_event(task_text, start_time, end_time, duration.total_seconds()) 

                self.pending = False

                del self.pending_tasks[task_text]

            self.save_tasks()
    
    def delete_task(self):
        task_index = self.task_list.curselection()
        if task_index:
            self.task_list.delete(task_index)
            self.save_tasks()
    
    def clear_placeholder(self, event):
        if self.task_input.get() == "Enter your todo here...":
            self.task_input.delete(0, tk.END)
            self.task_input.configure(style="TEntry")

    def restore_placeholder(self, event):
        if self.task_input.get() == "":
            self.task_input.insert(0, "Enter your todo here...")
            self.task_input.configure(style="Custom.TEntry")

    def load_tasks(self):
        try:
            with open("tasks.json", "r") as f:
                data = json.load(f)
                for task in data:
                    self.task_list.insert(tk.END, task["text"])
                    self.task_list.itemconfig(tk.END, fg=task["color"])
        except FileNotFoundError:
            pass
    
    def save_tasks(self):
        data = []
        for i in range(self.task_list.size()):
            text = self.task_list.get(i)
            color = self.task_list.itemcget(i, "fg")
            data.append({"text": text, "color": color})
        with open("tasks.json", "w") as f:
            json.dump(data, f)
    def connect(self):
        creds = None
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'client_secret_941071254740-11i8vn2vbis9apkcm1okqbe11he6b0ph.apps.googleusercontent.com.json', SCOPES)
                creds = flow.run_local_server(port=0)
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)
        self.service = build('calendar', 'v3', credentials=creds)
        return self.service



    
    def get_timezone(self):
        local_tz = tzlocal.get_localzone()
        local_tzname = local_tz.tzname(datetime.datetime.now(local_tz))
        return local_tzname



    def convert_to_RFC_datetime(self, dt):
        return dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")



    def create_event(self, summary, start_time, end_time, duration):
            if self.service:
                event = {
                    'summary': summary,
                    'description': f"Duration: {duration}",
                    'start': {'dateTime': start_time.isoformat(), 'timeZone': 'GMT'},
                    'end': {'dateTime': end_time.isoformat(), 'timeZone': 'GMT'},
                }
                event_result = self.service.events().insert(calendarId='primary', body=event).execute()
                print(f'Task {summary} is Done Adding it to calendar.... Well Done!')
            else:
                print("Google Calendar service not initialized.")

if __name__ == '__main__':
    app = TodoListApp()
    app.mainloop()
