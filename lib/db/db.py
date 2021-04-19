from os.path import isfile

from sqlite3 import connect

from apscheduler.triggers.cron import CronTrigger

DB_PATH = './data/db/database.db'
BUILD_PATH = './data/db/build.sql'

connection = connect(DB_PATH, check_same_thread = False)
curset = connection.cursor()

def commit(func):
    def inner(*args, **kwargs):
        func(*args, **kwargs)
        commit_run()
    return inner

@commit
def build():
    if isfile(BUILD_PATH):
        scriptexec(BUILD_PATH)

def commit_run():
    #print('[EnodestBot] Committing to the db...')
    connection.commit()

def close():
    connection.close()

def autosave(scheduler):
    scheduler.add_job(commit_run, CronTrigger(second = 0))

def field(command, *values):
    curset.execute(command, tuple(values))

    if (fetch := curset.fetchone()) is not None:
        return fetch[0]

def record(command, *values):
    curset.execute(command, tuple(values))

    return curset.fetchone()

def records(command, *values):
    curset.execute(command, tuple(values))

    return curset.fetchall()

def column(command, *values):
    curset.execute(command, tuple(values))

    return [item[0] for item in curset.fetchall()]

def execute(command, *values):
    curset.execute(command, tuple(values))

def multiexec(command, valueset):
    curset.executemany(command, valueset)

def scriptexec(path):
    with open(path, 'r', encoding = 'utf-8') as script:
        curset.executescript(script.read())