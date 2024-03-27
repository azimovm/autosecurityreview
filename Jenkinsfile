#!groovy
pipeline {  
    agent { node { label 'docker' } }
            
    stages {
        stage('Build') {
            agent {
                docker {
                    reuseNode true
                    image 'python:latest'
                }
            }
        
            steps {
                withEnv(["HOME=${env.WORKSPACE}"]){
                    sh 'python --version'
                    sh 'echo $HOME'
                    sh 'python -m pip install --proxy=server-proxy.corproot.net:8080 --no-cache-dir requests'
                    sh 'echo "the PWD is : ${PWD}"'
                }
            }
        }
        
        stage('Git Checkout') {
            agent {
                docker {
                    reuseNode true
                    image 'python:latest'
                }
            }
        
            steps {
                withEnv(["HOME=${env.WORKSPACE}"]){
                     script {
                        git branch: 'master',
                            credentialsId: 'oce',
                            url: 'ssh://git@git.swisscom.com:7999/~taanasaa/automaticlibrarydocumentation.git'
                    }
                    sh 'echo "the PWD is : ${PWD}"'
                    sh 'ls -la'
                    sh 'python --version'
                    sh 'pip install --upgrade pip'
                    sh 'pip install -r requirements.txt'
                    sh 'python main.py --ui False --team $TEAM'
                }
            }
        }

        stage('Show HTML') {
            steps {
                script {
                    // Copy the HTML file to a location accessible by Jenkins
                    sh 'cp output.html $JENKINS_HOME/html'

                    // Publish the HTML file as an artifact
                    archiveArtifacts artifacts: 'html/output.html', allowEmptyArchive: true
                }
            }
        }
        
        stage('Display HTML') {
            steps {
                // You can use a post-build action to display the HTML file
                // For example, you can use the "HTML Publisher Plugin" to publish the HTML file
                publishHTML(target: [
                    allowMissing: false,
                    alwaysLinkToLastBuild: false,
                    keepAll: true,
                    reportDir: 'html',
                    reportFiles: 'output.html',
                    reportName: 'My HTML Report'
                ])
            }
        }
    }
}