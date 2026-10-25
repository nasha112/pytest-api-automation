pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                git branch: 'master',
                    url: 'https://github.com/nasha112/pytest-api-automation.git'
            }
        }

        stage('Setup Python') {
            steps {
                bat '''
                    python -m venv venv
                    call venv\\Scripts\\activate.bat
                    python -m pip install --upgrade pip
                    pip install -r requirements.txt
                '''
            }
        }

        stage('Run Tests') {
            steps {
                bat '''
                    mkdir reports allure-results
                    venv\\Scripts\\python -m pytest --ignore=tests/local --maxfail=1 --disable-warnings -q --alluredir=allure-results --junitxml=allure-results/junit-results.xml
                '''
            }
        }

        stage('Archive Results') {
            steps {
                archiveArtifacts artifacts: 'allure-results/**', allowEmptyArchive: true
                junit 'allure-results/junit-results.xml'
            }
        }

        stage('Allure Report') {
            steps {
                allure includeProperties: false, jdk: '', results: [[path: 'allure-results']]
            }
        }
    }
}
