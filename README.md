# Pizarra

A web app in Python 3.x to manage Parallel Programming Competitions based on [Tablón](https://trasgo.infor.uva.es/tablon/)

## Features

- Account
  - [x] login / logout
  - [x] register
  - [x] change password
  - [x] regenerate access token
  - [x] your group
  - [x] activity
  - [x] join a new team 
  - [x] switch language
- Dashboard
  - Student
    - [x] summaries
    - [x] latest requests
    - [x] latest badge / no badges
    - [x] your team / no team
  - Admin
    - requests
      - [x] list
      - [x] view
      - [x] remove
    - students
      - [x] list
      - [x] remove
      - [x] reset password
      - [x] import csv
    - assignments
      - [x] list
      - [x] view
      - [x] remove
      - [x] create
      - [x] edit
      - [ ] attachments
    - groups
      - [x] list
      - [x] remove
      - [ ] edit
    - badges
      - [ ] list
      - [ ] create
      - [ ] edit
      - [ ] logic to assign them to users
    - [ ] manage RQ task scheduler
    - [ ] summaries ? 
    - [ ] global status ?
- Assignments
  - [x] list
  - [x] info
  - [x] submit
  - [x] badges to obtain
- Requests
  - [x] list
  - [x] filter
  - [x] info
- LeaderBoard
  - [ ] view
- FAQ
  - [ ] info
- RQ
  - [x] enqueue
  - [x] check for malicious code
  - [x] compile
  - [x] local execution
  - [x] update status
  - [x] update user quota
  - [x] update points to request and user 
  - [ ] verify results with inputs
- Docker
  - [x] Dockerfile
  - [x] docker-compose
  - [ ] support for gunicorn
  

## Other features

- Localization
  - [X] English
  - [ ] Spanish (WIP)

## Screenshots

- Dashboard Student

![Dashboard Student with Team and Latest Badge!](/app/base/static/assets/pizarra/img/readme/dashboard-full.png "Dashboard Student")
![Dashboard Student with no Team and Badge!](/app/base/static/assets/pizarra/img/readme/dashboard-empty.png "Dashboard Student")

- My Account

![My Account Group!](/app/base/static/assets/pizarra/img/readme/my-account-group.png "My Account")
![My Account Access Key!](/app/base/static/assets/pizarra/img/readme/my-account-access-key.png "My Account")
![My Account Badges!](/app/base/static/assets/pizarra/img/readme/my-account-badges.png "My Account")

- Requests

![Request List!](/app/base/static/assets/pizarra/img/readme/requests-list.png "Request List")

- Assignments

![Assignment Info!](/app/base/static/assets/pizarra/img/readme/assignment-info.png "Assignment")
![Assignment New!](/app/base/static/assets/pizarra/img/readme/assignment-new.png "Assignment")
![Assignment Submit!](/app/base/static/assets/pizarra/img/readme/assignment-submit-example.png "Assignment")

- Task Scheduler

![Task Scheduler!](/app/base/static/assets/pizarra/img/readme/rq-task-scheduler.png "Task Scheduler")


## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See deployment for notes on how to deploy the project on a live system.

### Prerequisites

What things you need to install the software and how to install them

```
TODO Dockerfile
```

### Installing

A step by step series of examples that tell you how to get a development env running

```
TODO full guide
```

```
pip install -r requirements.txt 
python run.py
```

## Deployment

```
TODO
```

## Built With

* [Flask](https://flask.palletsprojects.com/en/1.1.x/) - as micro framework for the web app
* [Flask Dashboard AdminLTE](https://github.com/app-generator/flask-dashboard-adminlte) - for Dashboard template
* [Redis Queue](https://python-rq.org/) - for Task Scheduling

## Contributing


## Versioning

## Authors

* **Nicolas Martini** - *Initial work* - [nimar3](https://github.com/nimar3)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details

## Acknowledgments

```
TODO
```
