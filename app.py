from flask import Flask, render_template, request, redirect, url_for
import csv
import os
from datetime import datetime, timezone

app = Flask(__name__)

def load_data():
    if os.path.exists('data/streaks.csv'):
        with open('data/streaks.csv', mode='r') as f:
            reader = csv.DictReader(f)
            return sorted(list(reader), key=lambda x: datetime.strptime(x['Date'], '%Y-%m-%d'), reverse=True)
    return []

def save_data(data):
    with open('data/streaks.csv', mode='w', newline='') as f:
        fieldnames = ['Date', 'Saketh', 'Saketh_Difficulty', 'Aditya', 'Aditya_Difficulty', 'Kushagra', 'Kushagra_Difficulty']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

def convert_to_leetcode_url(question_text):
    if ". " in question_text:
        question_title = question_text.split(". ", 1)[1].strip().lower().replace(" ", "-")
        return f"https://leetcode.com/problems/{question_title}"
    return None  

def add_default_entry_if_new_day(data):
    today = datetime.now(timezone.utc).date()
    today_str = today.strftime('%Y-%m-%d')
    existing_dates = {entry['Date'] for entry in data}

    # If today is not in the existing dates, add a new entry
    if today_str not in existing_dates:
        data.append({
            'Date': today_str,
            'Saketh': '',
            'Saketh_Difficulty': None,
            'Aditya': '',
            'Aditya_Difficulty': None,
            'Kushagra': '',
            'Kushagra_Difficulty': None
        })
        save_data(data)  # Save the new entry to the CSV file

@app.route('/')
def index():
    data = load_data()
    add_default_entry_if_new_day(data)  # Check and add default entry for today

    # Generate links and structure question data
    for entry in data:
        entry['Saketh_questions'] = []
        entry['Aditya_questions'] = []
        entry['Kushagra_questions'] = []

        for q, d in zip(entry['Saketh'].split(','), entry['Saketh_Difficulty'].split(',')):
            if entry['Saketh']:
                question_url = convert_to_leetcode_url(q)
                entry['Saketh_questions'].append((q.strip(), question_url, d.strip()))

        for q, d in zip(entry['Aditya'].split(','), entry['Aditya_Difficulty'].split(',')):
            if entry['Aditya']:
                question_url = convert_to_leetcode_url(q)
                entry['Aditya_questions'].append((q.strip(), question_url, d.strip()))

        for q, d in zip(entry['Kushagra'].split(','), entry['Kushagra_Difficulty'].split(',')):
            if entry['Kushagra']:
                question_url = convert_to_leetcode_url(q)
                entry['Kushagra_questions'].append((q.strip(), question_url, d.strip()))

    return render_template('index5.html', data=data)

@app.route('/add', methods=['POST'])
def add():
    date = datetime.now().date().strftime('%Y-%m-%d')
    saketh = request.form.get('saketh', '').strip()
    saketh_difficulty = request.form.get('saketh_difficulty', None)
    aditya = request.form.get('aditya', '').strip()
    aditya_difficulty = request.form.get('aditya_difficulty', None)
    kushagra = request.form.get('kushagra', '').strip()
    kushagra_difficulty = request.form.get('kushagra_difficulty', None)

    data = load_data()
    entry_found = False

    for entry in data:
        if entry['Date'] == date:
            entry_found = True
            if saketh:
                entry['Saketh'] = f"{entry['Saketh']}, {saketh}" if entry['Saketh'] else saketh
                entry['Saketh_Difficulty'] = f"{entry['Saketh_Difficulty']}, {saketh_difficulty}" if entry['Saketh_Difficulty'] and saketh_difficulty != None else saketh_difficulty
            if aditya:
                entry['Aditya'] = f"{entry['Aditya']}, {aditya}" if entry['Aditya'] else aditya
                entry['Aditya_Difficulty'] = f"{entry['Aditya_Difficulty']}, {aditya_difficulty}" if entry['Aditya_Difficulty'] and aditya_difficulty != None else aditya_difficulty
            if kushagra:
                entry['Kushagra'] = f"{entry['Kushagra']}, {kushagra}" if entry['Kushagra'] else kushagra
                entry['Kushagra_Difficulty'] = f"{entry['Kushagra_Difficulty']}, {kushagra_difficulty}" if entry['Kushagra_Difficulty'] and kushagra_difficulty != None else kushagra_difficulty
            break

    if not entry_found:
        data.append({
            'Date': date,
            'Saketh': saketh,
            'Saketh_Difficulty': saketh_difficulty,
            'Aditya': aditya,
            'Aditya_Difficulty': aditya_difficulty,
            'Kushagra': kushagra,
            'Kushagra_Difficulty': kushagra_difficulty
        })

    save_data(data)
    return redirect(url_for('index'))

@app.route('/delete_question', methods=['POST'])
def delete_question():
    date = request.form['date']
    question = request.form['question']
    role = request.form['role']

    data = load_data()
    
    for entry in data:
        if entry['Date'] == date:
            # Remove the specific question from the appropriate list
            questions = entry[role].split(',')
            difficulties = entry[f'{role}_Difficulty'].split(',')
            if question in questions:
                index = questions.index(question)
                questions.pop(index)
                difficulties.pop(index)
                
                entry[role] = ', '.join(questions)
                entry[f'{role}_Difficulty'] = ', '.join(difficulties) if difficulties else None
                break

    save_data(data)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
