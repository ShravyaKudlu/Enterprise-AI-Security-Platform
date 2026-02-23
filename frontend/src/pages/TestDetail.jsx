import React, { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import {
  Box, Typography, Paper, Tabs, Tab, Grid, Card, CardContent,
  Chip, Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  LinearProgress, Alert, CircularProgress, Button, Divider
} from '@mui/material'
import DownloadIcon from '@mui/icons-material/Download'
import { useQuery } from 'react-query'
import { securityTestAPI } from '../api/securityTests'

function TestDetail() {
  const { testId } = useParams()
  const [activeTab, setActiveTab] = useState(0)
  const [progress, setProgress] = useState(null)

  const { data: testStatus, refetch: refetchStatus } = useQuery(
    ['testStatus', testId],
    () => securityTestAPI.getTestStatus(testId),
    { 
      refetchInterval: 2000,
      refetchIntervalInBackground: true,
      retry: true,
      retryDelay: 1000
    }
  )

  const { data: testResults, isLoading: isLoadingResults } = useQuery(
    ['testResults', testId],
    () => securityTestAPI.getTestResults(testId)
  )

  const { data: analytics } = useQuery(
    ['testAnalytics', testId],
    () => securityTestAPI.getTestAnalytics(testId),
    { enabled: testStatus?.data?.status === 'completed' }
  )

  useEffect(() => {
    if (testStatus?.data) {
      setProgress(testStatus.data.progress)
    }
  }, [testStatus])

  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue)
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return 'success'
      case 'running': return 'warning'
      case 'failed': return 'error'
      case 'queued': return 'info'
      default: return 'default'
    }
  }

  if (isLoadingResults) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
        <CircularProgress />
      </Box>
    )
  }

  const test = testResults?.data

  // Check for vulnerabilities
  const hasVulnerabilities = test?.runs?.some(run => run.evaluation?.leakage_detected)
  const vulnerabilityCount = test?.runs?.filter(run => run.evaluation?.leakage_detected).length || 0

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Test: {test?.test_name}
      </Typography>

      {!testStatus?.data && (
        <Alert severity="warning" sx={{ mb: 2 }}>
          <Typography variant="h6">Loading test status...</Typography>
          <Typography>Please wait while we fetch the test information.</Typography>
        </Alert>
      )}

      {(testStatus?.data?.status === 'running' || testStatus?.data?.status === 'queued') && (
        <Paper elevation={3} sx={{ mb: 3, p: 3, bgcolor: 'info.light', border: '2px solid', borderColor: 'info.main' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
            <CircularProgress size={30} sx={{ mr: 2, color: 'info.dark' }} />
            <Typography variant="h5" sx={{ fontWeight: 'bold', color: 'info.dark' }}>
              Test in Progress - Please Wait...
            </Typography>
          </Box>
          <Typography variant="body1" sx={{ mb: 2, fontSize: '1.1rem' }}>
            <strong>{progress?.completed_runs || 0}</strong> of <strong>{progress?.total_runs || 0}</strong> runs completed 
            (<strong>{Math.round(progress?.percent_complete || 0)}%</strong>)
          </Typography>
          
          <Box sx={{ position: 'relative', mb: 2 }}>
            <LinearProgress 
              variant="determinate" 
              value={progress?.percent_complete || 0}
              sx={{ 
                height: 20, 
                borderRadius: 2,
                backgroundColor: 'grey.400',
                '& .MuiLinearProgress-bar': {
                  backgroundColor: 'info.main',
                  borderRadius: 2
                }
              }}
            />
            <Typography 
              variant="body2" 
              sx={{ 
                position: 'absolute', 
                top: '50%', 
                left: '50%', 
                transform: 'translate(-50%, -50%)',
                fontWeight: 'bold',
                color: 'white',
                textShadow: '1px 1px 2px rgba(0,0,0,0.5)'
              }}
            >
              {Math.round(progress?.percent_complete || 0)}%
            </Typography>
          </Box>
          
          <Box sx={{ mt: 2 }}>
            <Grid container spacing={2}>
              <Grid item xs={4}>
                <Typography variant="body2" color="text.secondary">
                  Completed: <strong>{progress?.completed_runs || 0}</strong>
                </Typography>
              </Grid>
              <Grid item xs={4} textAlign="center">
                <Typography variant="body2" color="text.secondary">
                  Failed: <strong>{progress?.failed_runs || 0}</strong>
                </Typography>
              </Grid>
              <Grid item xs={4} textAlign="right">
                <Typography variant="body2" color="text.secondary">
                  Remaining: <strong>{Math.max(0, (progress?.total_runs || 0) - (progress?.completed_runs || 0))}</strong>
                </Typography>
              </Grid>
            </Grid>
            
            <Box sx={{ mt: 1, display: 'flex', justifyContent: 'center' }}>
              <Chip 
                label={progress?.estimated_remaining_seconds > 0 
                  ? `⏱️ ${Math.round(progress.estimated_remaining_seconds)}s remaining`
                  : '⏱️ Calculating time...'
                }
                color="info"
                size="small"
                sx={{ fontWeight: 'bold' }}
              />
            </Box>
            
            {progress?.avg_time_per_run > 0 && (
              <Typography variant="caption" color="text.secondary" sx={{ display: 'block', textAlign: 'center', mt: 0.5 }}>
                Avg: {Math.round(progress.avg_time_per_run)}s per test
              </Typography>
            )}
          </Box>
        </Paper>
      )}

      {testStatus?.data?.status === 'completed' && hasVulnerabilities && (
        <Alert severity="error" sx={{ mb: 2 }}>
          <Typography variant="h6" gutterBottom>
            VULNERABILITY DETECTED
          </Typography>
          <Typography variant="body1">
            <strong>{vulnerabilityCount}</strong> security issue{vulnerabilityCount > 1 ? 's' : ''} detected in this test.
          </Typography>
          <Typography variant="body2" sx={{ mt: 1 }}>
            Data leakage was identified. Review the Findings tab for detailed information about the vulnerabilities.
          </Typography>
        </Alert>
      )}

      {testStatus?.data?.status === 'completed' && !hasVulnerabilities && (
        <Alert severity="success" sx={{ mb: 2 }}>
          <Typography variant="h6" gutterBottom>
            NO VULNERABILITIES DETECTED
          </Typography>
          <Typography variant="body1">
            All models properly protected data boundaries.
          </Typography>
          <Typography variant="body2" sx={{ mt: 1 }}>
            The tested models showed appropriate data isolation and no leakage was detected.
          </Typography>
        </Alert>
      )}

      <Paper sx={{ mb: 2 }}>
        <Tabs value={activeTab} onChange={handleTabChange}>
          <Tab label="Summary" />
          <Tab label="Results" />
          <Tab label="Findings" />
          <Tab label="Export" />
        </Tabs>

        <Box sx={{ p: 3 }}>
          {activeTab === 0 && (
            <Grid container spacing={3}>
              {hasVulnerabilities && (
                <Grid item xs={12}>
                  <Card sx={{ bgcolor: 'error.light', color: 'error.contrastText' }}>
                    <CardContent>
                      <Typography variant="h5" gutterBottom>
                        Security Issues Found
                      </Typography>
                      <Typography variant="body1">
                        <strong>{vulnerabilityCount}</strong> data leakage incident{vulnerabilityCount > 1 ? 's' : ''} detected
                      </Typography>
                      {analytics?.data && (
                        <>
                          <Typography sx={{ mt: 1 }}>
                            <strong>Attack Success Rate:</strong> {analytics.data.attack_success_rate}%
                          </Typography>
                          <Typography>
                            <strong>Highest Risk Level:</strong>{' '}
                            {test?.runs
                              ?.filter(r => r.evaluation?.leakage_detected)
                              .reduce((max, r) => {
                                const levels = { 'CRITICAL': 4, 'HIGH': 3, 'MEDIUM': 2, 'LOW': 1 }
                                return levels[r.evaluation.risk_level] > levels[max] ? r.evaluation.risk_level : max
                              }, 'LOW')}
                          </Typography>
                        </>
                      )}
                      <Typography variant="body2" sx={{ mt: 2 }}>
                        Switch to the "Findings" tab to review detailed vulnerability information.
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              )}

              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>Test Information</Typography>
                    <Typography><strong>Status:</strong>{' '}
                      <Chip 
                        label={test?.status} 
                        color={getStatusColor(test?.status)}
                        size="small"
                      />
                    </Typography>
                    <Typography><strong>Created:</strong> {test?.created_at && new Date(test.created_at).toLocaleString()}</Typography>
                    <Typography><strong>Total Runs:</strong> {test?.total_runs}</Typography>
                    {analytics?.data && (
                      <>
                        <Typography><strong>Attack Success Rate:</strong> {analytics.data.attack_success_rate}%</Typography>
                        <Typography><strong>Leakage Incidents:</strong> {analytics.data.leakage_detected_count}</Typography>
                      </>
                    )}
                  </CardContent>
                </Card>
              </Grid>

              {analytics?.data?.risk_distribution && (
                <Grid item xs={12} md={6}>
                  <Card>
                    <CardContent>
                      <Typography variant="h6" gutterBottom>Risk Distribution</Typography>
                      {Object.entries(analytics.data.risk_distribution).map(([level, count]) => (
                        <Box key={level} sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                          <Typography>{level}</Typography>
                          <Chip 
                            label={count} 
                            size="small"
                            color={level === 'CRITICAL' ? 'error' : level === 'HIGH' ? 'warning' : 'default'}
                          />
                        </Box>
                      ))}
                    </CardContent>
                  </Card>
                </Grid>
              )}

              {analytics?.data?.vendor_comparison && (
                <Grid item xs={12}>
                  <Card>
                    <CardContent>
                      <Typography variant="h6" gutterBottom>Vendor Comparison</Typography>
                      <TableContainer>
                        <Table size="small">
                          <TableHead>
                            <TableRow>
                              <TableCell>Vendor</TableCell>
                              <TableCell>Runs</TableCell>
                              <TableCell>Leakage</TableCell>
                              <TableCell>Rate</TableCell>
                              <TableCell>Avg Risk</TableCell>
                            </TableRow>
                          </TableHead>
                          <TableBody>
                            {Object.entries(analytics.data.vendor_comparison).map(([vendor, data]) => (
                              <TableRow key={vendor}>
                                <TableCell>{vendor}</TableCell>
                                <TableCell>{data.total_runs}</TableCell>
                                <TableCell>{data.leakage_count}</TableCell>
                                <TableCell>{data.leakage_rate}%</TableCell>
                                <TableCell>{data.avg_risk_score}</TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      </TableContainer>
                    </CardContent>
                  </Card>
                </Grid>
              )}
            </Grid>
          )}

          {activeTab === 1 && (
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Run ID</TableCell>
                    <TableCell>Model</TableCell>
                    <TableCell>Vendor</TableCell>
                    <TableCell>Technique</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Risk Score</TableCell>
                    <TableCell>Leakage</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {test?.runs?.map((run) => (
                    <TableRow key={run.run_id}>
                      <TableCell>{run.run_id}</TableCell>
                      <TableCell>{run.model_name}</TableCell>
                      <TableCell>{run.model_vendor}</TableCell>
                      <TableCell>{run.technique}</TableCell>
                      <TableCell>
                        <Chip 
                          label={run.status}
                          size="small"
                          color={getStatusColor(run.status)}
                        />
                      </TableCell>
                      <TableCell>
                        {run.evaluation ? (
                          <Chip 
                            label={run.evaluation.risk_score || 'N/A'}
                            size="small"
                            color={run.evaluation.risk_level === 'CRITICAL' ? 'error' : 
                                   run.evaluation.risk_level === 'HIGH' ? 'warning' : 'default'}
                          />
                        ) : 'Pending'}
                      </TableCell>
                      <TableCell>
                        {run.evaluation?.leakage_detected ? (
                          <Chip label="YES" color="error" size="small" />
                        ) : run.evaluation ? (
                          <Chip label="NO" color="success" size="small" />
                        ) : (
                          'Pending'
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}

          {activeTab === 2 && (
            <Box>
              {test?.runs?.filter(r => r.evaluation?.leakage_detected).length === 0 ? (
                <Alert severity="success">
                  <Typography variant="h6">No Vulnerabilities Found</Typography>
                  <Typography>
                    No leakage detected in this test. All models properly protected data boundaries.
                  </Typography>
                </Alert>
              ) : (
                <>
                  <Alert severity="error" sx={{ mb: 3 }}>
                    <Typography variant="h6">VULNERABILITY DETECTED</Typography>
                    <Typography>
                      {test?.runs?.filter(r => r.evaluation?.leakage_detected).length} security issue(s) found. 
                      Review the detailed findings below.
                    </Typography>
                  </Alert>
                  <Grid container spacing={2}>
                    {test?.runs
                      ?.filter(r => r.evaluation?.leakage_detected)
                      .map((run) => (
                        <Grid item xs={12} key={run.run_id}>
                          <Card variant="outlined" sx={{ borderColor: 'error.main', borderWidth: 2, mb: 2 }}>
                            <CardContent>
                              <Typography variant="h5" gutterBottom color="error" sx={{ fontWeight: 'bold' }}>
                                Finding #{run.run_id} - VULNERABILITY DETECTED
                              </Typography>
                              <Divider sx={{ my: 2 }} />
                              <Grid container spacing={2}>
                                <Grid item xs={12} md={6}>
                                  <Typography variant="subtitle1" gutterBottom><strong>Test Details:</strong></Typography>
                                  <Typography><strong>Model:</strong> {run.model_name}</Typography>
                                  <Typography><strong>Vendor:</strong> {run.model_vendor}</Typography>
                                  <Typography><strong>Technique:</strong> {run.technique}</Typography>
                                  <Typography>
                                    <strong>Risk Score:</strong>{' '}
                                    <Chip 
                                      label={`${run.evaluation.risk_score} / 10`}
                                      color={run.evaluation.risk_level === 'CRITICAL' || run.evaluation.risk_level === 'HIGH' ? 'error' : 'warning'}
                                      size="small"
                                    />
                                  </Typography>
                                  <Typography><strong>Risk Level:</strong> {run.evaluation.risk_level}</Typography>
                                  <Typography><strong>Categories:</strong>{' '}
                                    {run.evaluation.categories?.join(', ')}
                                  </Typography>
                                </Grid>
                                <Grid item xs={12} md={6}>
                                  <Typography variant="subtitle1" gutterBottom><strong>Evidence:</strong></Typography>
                                  <Box sx={{ p: 2, bgcolor: 'error.light', borderRadius: 1, border: '1px solid', borderColor: 'error.main' }}>
                                    <Typography variant="body2" color="error.dark" sx={{ fontWeight: 'bold', mb: 1 }}>
                                      Model Response (Evidence of Leakage):
                                    </Typography>
                                    <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', fontFamily: 'monospace' }}>
                                      {run.response_text || run.response_preview || 'No response text available'}
                                    </Typography>
                                  </Box>
                                </Grid>
                              </Grid>
                            </CardContent>
                          </Card>
                        </Grid>
                      ))}
                  </Grid>
                </>
              )}
            </Box>
          )}

          {activeTab === 3 && (
            <Box>
              <Typography variant="h6" gutterBottom>Export Test Results</Typography>
              <Typography variant="body1" sx={{ mb: 3 }}>
                Download the complete test results for reporting and analysis.
              </Typography>
              
              <Grid container spacing={2}>
                <Grid item xs={12} md={4}>
                  <Card>
                    <CardContent>
                      <Typography variant="h6" gutterBottom>JSON Export</Typography>
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                        Complete test data including all responses and evaluations. Suitable for SIEM integration.
                      </Typography>
                      <Button 
                        variant="contained" 
                        startIcon={<DownloadIcon />}
                        onClick={() => {
                          const data = JSON.stringify(test, null, 2)
                          const blob = new Blob([data], { type: 'application/json' })
                          const url = URL.createObjectURL(blob)
                          const a = document.createElement('a')
                          a.href = url
                          a.download = `test-${testId}-results.json`
                          a.click()
                        }}
                        fullWidth
                      >
                        Download JSON
                      </Button>
                    </CardContent>
                  </Card>
                </Grid>
                
                <Grid item xs={12} md={4}>
                  <Card>
                    <CardContent>
                      <Typography variant="h6" gutterBottom>CSV Export</Typography>
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                        Tabular format with all runs and results. Easy to open in Excel.
                      </Typography>
                      <Button 
                        variant="contained" 
                        startIcon={<DownloadIcon />}
                        onClick={() => {
                          const headers = ['Run ID', 'Model', 'Vendor', 'Technique', 'Status', 'Risk Score', 'Risk Level', 'Leakage Detected', 'Categories']
                          const rows = test?.runs?.map(run => [
                            run.run_id,
                            run.model_name,
                            run.model_vendor,
                            run.technique,
                            run.status,
                            run.evaluation?.risk_score || 'N/A',
                            run.evaluation?.risk_level || 'N/A',
                            run.evaluation?.leakage_detected ? 'YES' : 'NO',
                            run.evaluation?.categories?.join('; ') || 'None'
                          ])
                          const csv = [headers, ...rows].map(row => row.join(',')).join('\n')
                          const blob = new Blob([csv], { type: 'text/csv' })
                          const url = URL.createObjectURL(blob)
                          const a = document.createElement('a')
                          a.href = url
                          a.download = `test-${testId}-results.csv`
                          a.click()
                        }}
                        fullWidth
                      >
                        Download CSV
                      </Button>
                    </CardContent>
                  </Card>
                </Grid>
                
                <Grid item xs={12} md={4}>
                  <Card>
                    <CardContent>
                      <Typography variant="h6" gutterBottom>Vulnerabilities Only</Typography>
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                        Export only the findings with vulnerabilities detected. Focus on issues.
                      </Typography>
                      <Button 
                        variant="contained" 
                        color="error"
                        startIcon={<DownloadIcon />}
                        onClick={() => {
                          const vulnerableRuns = test?.runs?.filter(r => r.evaluation?.leakage_detected)
                          const data = JSON.stringify({
                            test_name: test?.test_name,
                            test_id: testId,
                            vulnerability_count: vulnerableRuns?.length,
                            findings: vulnerableRuns
                          }, null, 2)
                          const blob = new Blob([data], { type: 'application/json' })
                          const url = URL.createObjectURL(blob)
                          const a = document.createElement('a')
                          a.href = url
                          a.download = `test-${testId}-vulnerabilities.json`
                          a.click()
                        }}
                        fullWidth
                      >
                        Download Vulnerabilities
                      </Button>
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>
            </Box>
          )}
        </Box>
      </Paper>
    </Box>
  )
}

export default TestDetail