pipeline {
    agent any

    stages {
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
                bat '''
                    allure generate allure-results -o _site --clean
                '''
            }
        }
    }
}
