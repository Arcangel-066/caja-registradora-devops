pipeline {
    agent any

    stages {
        stage('Clonar repositorio') {
            steps {
git branch: 'main', url: 'https://github.com/Arcangel-066/caja-registradora-devops.git'            
}
        }

        stage('Construir imagen Docker') {
            steps {
                sh 'docker build -t caja-registradora:latest .'
            }
        }

        stage('Desplegar aplicación') {
            steps {
                sh '''
                    docker rm -f caja-app || true

                    docker run -d \
                      --name caja-app \
                      -p 5000:5000 \
                      -v caja-datos:/app/data \
                      caja-registradora:latest
                '''
            }
        }
    }
}
