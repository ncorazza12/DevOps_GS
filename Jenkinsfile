pipeline {
    agent any

    options {
        skipDefaultCheckout(true)
        timestamps()
        timeout(time: 30, unit: 'MINUTES')
    }

    triggers {
        pollSCM('H/2 * * * *')
    }

    environment {
        IMAGE_NAME = 'ncorazza12/civictech-api'
        APP_URL    = 'http://host.docker.internal:8000'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
                script {
                    env.GIT_SHORT = sh(returnStdout: true, script: 'git rev-parse --short=7 HEAD').trim()
                    env.IMAGE_TAG = "${env.BUILD_NUMBER}-${env.GIT_SHORT}"
                    echo "Imagem: ${env.IMAGE_NAME}:${env.IMAGE_TAG}"
                }
            }
        }

        stage('Testes automatizados') {
            steps {
                sh '''
                    python3 -m venv .venv
                    . .venv/bin/activate
                    pip install --quiet -r requirements-dev.txt
                    pytest --cov=app --cov-report=xml --cov-report=term --junitxml=pytest-report.xml
                '''
            }
            post {
                always { junit allowEmptyResults: true, testResults: 'pytest-report.xml' }
            }
        }

        stage('Análise SonarQube') {
            steps {
                script {
                    def scannerHome = tool 'SonarScanner'
                    withSonarQubeEnv('sonarqube') {
                        sh "${scannerHome}/bin/sonar-scanner"
                    }
                }
            }
        }

        stage('Quality Gate') {
            steps {
                timeout(time: 5, unit: 'MINUTES') {
                    waitForQualityGate abortPipeline: true
                }
            }
        }

        stage('Docker Build') {
            steps {
                sh '''
                    docker build -t "$IMAGE_NAME:$IMAGE_TAG" -t "$IMAGE_NAME:latest" .
                '''
            }
        }

        stage('Trivy') {
            steps {
                sh '''
                    trivy image --no-progress --severity HIGH,CRITICAL --format table --output trivy-report.txt  "$IMAGE_NAME:$IMAGE_TAG"
                    trivy image --no-progress --severity HIGH,CRITICAL --format json  --output trivy-report.json "$IMAGE_NAME:$IMAGE_TAG"
                    cat trivy-report.txt
                    trivy image --no-progress --severity CRITICAL --exit-code 1 "$IMAGE_NAME:$IMAGE_TAG"
                '''
            }
            post {
                always { archiveArtifacts artifacts: 'trivy-report.*', allowEmptyArchive: true }
            }
        }

        stage('Publicação da imagem') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'dockerhub-creds',
                                                  usernameVariable: 'DH_USER',
                                                  passwordVariable: 'DH_PASS')]) {
                    sh '''
                        echo "$DH_PASS" | docker login -u "$DH_USER" --password-stdin
                        docker push "$IMAGE_NAME:$IMAGE_TAG"
                        docker push "$IMAGE_NAME:latest"
                    '''
                }
            }
        }

        stage('Deploy') {
            steps {
                sh '''
                    docker compose -p civictech pull
                    docker compose -p civictech up -d --no-build --remove-orphans
                    docker ps --filter name=civictech-api
                '''
            }
        }

        stage('Validação funcional') {
            steps {
                sh '''
                    ok=0
                    for i in $(seq 1 15); do
                        if curl -fsS "$APP_URL/health"; then ok=1; break; fi
                        echo "aguardando aplicação... ($i)"; sleep 3
                    done
                    if [ "$ok" != "1" ]; then docker logs civictech-api; exit 1; fi
                    echo
                    curl -fsS "$APP_URL/ocorrencias"
                '''
            }
        }
    }

    post {
        always { sh 'docker logout || true' }
        success { echo "Pipeline OK: $IMAGE_NAME:$IMAGE_TAG" }
        failure { echo 'Pipeline falhou: veja o estágio em vermelho.' }
    }
}