pipeline {
  agent any

  environment {
    AWS_REGION   = 'us-west-2'
    ECR_REGISTRY = '325054521915.dkr.ecr.us-west-2.amazonaws.com'
    ECR_REPO     = "${ECR_REGISTRY}/myapp"
    IMAGE_TAG    = "${env.BUILD_NUMBER}"
    AI_API_KEY   = credentials('AI_API_KEY')
    ALERT_EMAIL  = credentials('ALERT_EMAIL')   // Jenkins "Secret text" credential, keeps your address out of GitHub
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
      // 1) Collect the log tail, the AI answer and the main error lines
      sh '''
        tail -150 /var/lib/jenkins/jobs/${JOB_NAME}/builds/${BUILD_NUMBER}/log > build.log || true
        echo "===== AI ANALYSIS ====="
        python3 ai/analyze_failure.py build.log 2>&1 | tee ai_analysis.txt || true
        grep -iE "error|denied|not found|failed" build.log | tail -15 > error_summary.txt || true
        [ -s ai_analysis.txt ] || echo "AI analysis not available." > ai_analysis.txt
        [ -s error_summary.txt ] || echo "No error lines found in the log tail." > error_summary.txt
      '''

      // 2) Email it
      script {
        def aiText  = readFile('ai_analysis.txt')
        def errText = readFile('error_summary.txt')
        emailext(
          to: env.ALERT_EMAIL,
          subject: "FAILED: ${env.JOB_NAME} #${env.BUILD_NUMBER}",
          mimeType: 'text/plain',
          body: """Build FAILED

Job:    ${env.JOB_NAME}
Build:  #${env.BUILD_NUMBER}
Link:   ${env.BUILD_URL}console

----- MAIN ERROR LINES -----
${errText}

----- AI ANALYSIS -----
${aiText}

(Sent automatically by Jenkins)
"""
        )
      }
    }

    cleanup { deleteDir() }
  }
}