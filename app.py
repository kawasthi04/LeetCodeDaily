import os
import json
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from flask import Flask, request, render_template, redirect, url_for
from config import DATA_FILE_PATH

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)

USERS_FILE_PATH = 'data/users.json'

def load_users() -> List[str]:
    try:
        if os.path.exists(USERS_FILE_PATH):
            with open(USERS_FILE_PATH, 'r') as f:
                users = json.load(f)
                return users
    except Exception as e:
        logging.error(f"Error loading users: {e}")
    return []

def save_users(users: List[str]) -> None:
    try:
        with open(USERS_FILE_PATH, 'w') as f:
            json.dump(users, f, indent=4)
    except Exception as e:
        logging.error(f"Error saving users: {e}")

def convert_to_leetcode_url(question_text: str) -> Optional[str]:
    if ". " in question_text:
        question_title = question_text.split(". ", 1)[1]
        question_title = question_title.strip().lower().replace(" ", "-")
        return f"https://leetcode.com/problems/{question_title}"
    return None

def load_data() -> List[Dict[str, Any]]:
    try:
        if os.path.exists(DATA_FILE_PATH):
            with open(DATA_FILE_PATH, 'r') as f:
                data = json.load(f)
                data = sorted(
                    data,
                    key=lambda x: datetime.strptime(x['Date'], '%Y-%m-%d'),
                    reverse=True
                )
                return data
    except Exception as e:
        logging.error(f"Error loading data: {e}")
    return []

def save_data(data: List[Dict[str, Any]]) -> None:
    try:
        with open(DATA_FILE_PATH, 'w') as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        logging.error(f"Error saving data: {e}")

def add_default_entry_if_new_day(data: List[Dict[str, Any]]) -> None:
    today = datetime.now(timezone.utc).date()
    today_str = today.strftime('%Y-%m-%d')
    existing_dates = {entry['Date'] for entry in data}

    if today_str not in existing_dates:
        users = load_users()
        user_data = {
            user: {
                'Questions': [],
                'Difficulties': []
            } for user in users
        }
        data.append({
            'Date': today_str,
            'Users': user_data
        })
        save_data(data)

@app.route('/')
def index() -> str:
    data = load_data()
    add_default_entry_if_new_day(data)
    users = load_users()

    for entry in data:
        entry['User_questions'] = {}
        for user in users:
            entry['User_questions'][user] = []
            user_data = entry['Users'].get(user, {'Questions': [], 'Difficulties': []})
            questions = user_data['Questions']
            difficulties = user_data['Difficulties']
            for q, d in zip(questions, difficulties):
                question_url = convert_to_leetcode_url(q)
                entry['User_questions'][user].append((q.strip(), question_url, d.strip()))

    return render_template('index.html', data=data, users=users)

@app.route('/add', methods=['POST'])
def add() -> Any:
    date = datetime.now().date().strftime('%Y-%m-%d')
    users = load_users()
    data = load_data()
    entry_found = False

    for entry in data:
        if entry['Date'] == date:
            entry_found = True
            for user in users:
                question = request.form.get(f'{user.lower()}', '').strip()
                difficulty = request.form.get(f'{user.lower()}_difficulty', '')
                if question:
                    user_data = entry['Users'].setdefault(user, {'Questions': [], 'Difficulties': []})
                    user_data['Questions'].append(question)
                    user_data['Difficulties'].append(difficulty)
            break

    if not entry_found:
        user_data = {}
        for user in users:
            question = request.form.get(f'{user.lower()}', '').strip()
            difficulty = request.form.get(f'{user.lower()}_difficulty', '')
            user_data[user] = {
                'Questions': [question] if question else [],
                'Difficulties': [difficulty] if difficulty else []
            }

        data.append({
            'Date': date,
            'Users': user_data
        })

    save_data(data)
    return redirect(url_for('index'))

@app.route('/delete_question', methods=['POST'])
def delete_question() -> Any:
    date = request.form['date']
    question = request.form['question']
    user = request.form['user']

    data = load_data()

    for entry in data:
        if entry['Date'] == date:
            user_data = entry['Users'].get(user, {'Questions': [], 'Difficulties': []})
            if question in user_data['Questions']:
                index = user_data['Questions'].index(question)
                user_data['Questions'].pop(index)
                user_data['Difficulties'].pop(index)
                break

    save_data(data)
    return redirect(url_for('index'))

@app.route('/add_user', methods=['POST'])
def add_user() -> Any:
    new_user = request.form.get('new_user', '').strip()
    if new_user:
        users = load_users()
        if new_user not in users:
            users.append(new_user)
            save_users(users)

            data = load_data()
            for entry in data:
                entry['Users'][new_user] = {
                    'Questions': [],
                    'Difficulties': []
                }
            save_data(data)
    return redirect(url_for('index'))

@app.route('/delete_user', methods=['POST'])
def delete_user() -> Any:
    user_to_delete = request.form.get('user_to_delete', '').strip()
    if user_to_delete:
        users = load_users()
        if user_to_delete in users:
            users.remove(user_to_delete)
            save_users(users)

            data = load_data()
            for entry in data:
                if user_to_delete in entry['Users']:
                    del entry['Users'][user_to_delete]
            save_data(data)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run()