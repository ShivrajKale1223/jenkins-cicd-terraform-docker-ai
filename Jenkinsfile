pipeline {
  agent any

  environment {
    AWS_REGION = 'us-west-2'
    ECR_REGISTRY = '325054521915.dkr.ecr.us-west-2.amazonaws.com'
    ECR_REPO   = "${ECR_REGISTRY}/myapp"
    IMAGE_TAG  = "${env.BUILD_NUMBER}"
    AI_API_KEY = credentials('AI_API_KEY')
  }

  options {
    timestamps()
    timeout(time: 20, unit: 'MINUTES')
    buildDiscarder(logRotator(numToKeepStr: '5'))
  }

  stages {
    stage('Checkout') {
      steps { checkout scm }
    }

    stage('Build Image') {
      steps { sh 'docker build -t $ECR_REPO:$IMAGE_TAG ./app' }
    }

    stage('Security Scan') {
      steps {
        sh 'trivy image --exit-code 0 --severity HIGH,CRITICAL $ECR_REPO:$IMAGE_TAG'
      }
    }

    stage('Push to ECR') {
      steps {
        sh '''
          aws ecr get-login-password --region $AWS_REGION | \
            docker login --username AWS --password-stdin $ECR_REGISTRY
          docker push $ECR_REPO:$IMAGE_TAG
        '''
      }
    }

    stage('Deploy') {
      steps {
        sh '''
          docker stop myapp || true
          docker rm myapp || true
          docker run -d --name myapp --restart unless-stopped -p 80:5000 $ECR_REPO:$IMAGE_TAG
          sleep 5
          curl -f http://localhost/health
        '''
      }
    }
  }

  post {
    success { echo "Deployed build ${env.BUILD_NUMBER}" }
    failure {
      script {
        // Pull the last 150 lines of this build's console log
        def logText = currentBuild.rawBuild.getLog(150).join('\n')
        writeFile file: 'build.log', text: logText
        sh 'pip3 install -q --user requests || true'
        def analysis = sh(script: 'python3 ai/analyze_failure.py build.log', returnStdout: true).trim()
        echo "===== AI ANALYSIS =====\n${analysis}"
      }
    }
    always { cleanWs() }
  }
}