@Library('shared@main') _

standardAppPipeline([
  dockerWaitTimeout: 1800,
  registry: 'gitea.hdhomelab.com',
  credentialsId: 'gitea-registry',
  repository: 'cicd/tc-photo-grabber',
  pushLatest: true
])
