# Quiz Reminder Popup

A simple macOS utility that reminds you of a custom quiz after a timer expires. It uses a menu bar icon and stores your last settings under `~/Library/Application Support/QuizReminder/`.

## Features

- Enter a question, its answer and a timer value.
- Displays a popup when the timer ends asking for your answer. The window stays on top.
- Shows your answer and the correct one side by side.
- Menu bar icon to open settings, start/stop the timer and quit the app.
- macOS Notification Center alert when the timer ends.
- Settings are preserved between runs.

## Requirements

- Python 3
- Packages listed in `requirements.txt`

Install dependencies with:

```bash
pip install -r requirements.txt
```

## Running

Run the application with:

```bash
python quiz_reminder.py
```

The application uses `icon.icns` for its window and menu bar icon.

