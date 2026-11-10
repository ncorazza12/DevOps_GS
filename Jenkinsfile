node {
    def IMAGE_NAME = 'ncorazza12/civictech-api'
    def APP_URL    = 'http://host.docker.internal:8000'
    def IMAGE_TAG  = ""

    timestamps {
        timeout(time: 30, unit: 'MINUTES') {
            
            stage('Checkout') {
                checkout scm
                def gitShort = sh(returnStdout: true, script: 'git rev-parse --short=7 HEAD').trim()
                IMAGE_TAG = "${env.BUILD_NUMBER}-${gitShort}"
                echo "Imagem: ${IMAGE_NAME}:${IMAGE_TAG}"
            }

            stage('Testes automatizados') {
                try {
                    sh '''
                        python3 -m venv .venv
                        . .venv/bin/activate
                        pip install --quiet -r requirements-dev.txt
                        pytest --cov=app --cov-report=xml --cov-report=term --junitxml=pytest-report.xml
                    '''
                } finally {
                    junit allowEmptyResults: true, testResults: 'pytest-report.xml'
                }
            }

            stage('Análise SonarQube') {
                def scannerHome = tool 'SonarScanner'
                withSonarQubeEnv('sonarqube') {
                    sh "${scannerHome}/bin/sonar-scanner"
                }
            }

            stage('Quality Gate') {
                timeout(time: 5, unit: 'MINUTES') {
                    waitForQualityGate abortPipeline: true
                }
            }

            stage('Docker Build') {
                sh "docker build -t \"${IMAGE_NAME}:${IMAGE_TAG}\" -t \"${IMAGE_NAME}:latest\" ."
            }

            stage('Trivy') {
                try {
                    sh """
                        trivy image --no-progress --severity HIGH,CRITICAL --format table --output trivy-report.txt "${IMAGE_NAME}:${IMAGE_TAG}"
                        trivy image --no-progress --severity HIGH,CRITICAL --format json --output trivy-report.json "${IMAGE_NAME}:${IMAGE_TAG}"
                        cat trivy-report.txt
                        trivy image --no-progress --severity CRITICAL --exit-code 1 "${IMAGE_NAME}:${IMAGE_TAG}"
                    """
                } finally {
                    archiveArtifacts artifacts: 'trivy-report.*', allowEmptyArchive: true
                }
            }

            stage('Publicação da imagem') {
                withCredentials([usernamePassword(credentialsId: 'dockerhub-creds',
                                                  usernameVariable: 'DH_USER',
                                                  passwordVariable: 'DH_PASS')]) {
                    sh """
                        echo "\$DH_PASS" | docker login -u "\$DH_USER" --password-stdin
                        docker push "${IMAGE_NAME}:${IMAGE_TAG}"
                        docker push "${IMAGE_NAME}:latest"
                    """
                }
            }

            stage('Deploy') {
                sh '''
                    docker compose -p civictech pull
                    docker compose -p civictech up -d --no-build --remove-orphans
                    docker ps --filter name=civictech-api
                '''
            }

            stage('Validação funcional') {
                sh """
                    ok=0
                    for i in \$(seq 1 15); do
                        if curl -fsS "${APP_URL}/health"; then ok=1; break; fi
                        echo "aguardando aplicação... (\$i)"; sleep 3
                    done
                    if [ "\$ok" != "1" ]; then docker logs civictech-api; exit 1; fi
                    echo
                    curl -fsS "${APP_URL}/ocorrencias"
                """
            }
        }
    }
}