import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Box, Typography, Stepper, Step, StepLabel, Button,
  TextField, FormControl, InputLabel, Select, MenuItem,
  Checkbox, FormGroup, FormControlLabel, Card, CardContent,
  Grid, Chip, Slider, Alert, CircularProgress
} from '@mui/material'
import { securityTestAPI } from '../api/securityTests'

const steps = ['Test Configuration', 'Attack Scenario', 'Target Models', 'Review & Launch']

const AVAILABLE_MODELS = [
  { adapter: 'openai', model: 'gpt-4', name: 'GPT-4', type: 'public' },
  { adapter: 'openai', model: 'gpt-3.5-turbo', name: 'GPT-3.5 Turbo', type: 'public' },
  { adapter: 'anthropic', model: 'claude-3-opus-20240229', name: 'Claude 3 Opus', type: 'public' },
  { adapter: 'anthropic', model: 'claude-3-sonnet', name: 'Claude 3 Sonnet', type: 'public' },
  { adapter: 'google', model: 'gemini-1.5-pro', name: 'Gemini Pro', type: 'public' },
  { adapter: 'ollama', model: 'llama3.2', name: 'Llama 3.2 (Local)', type: 'local' },
  { adapter: 'ollama', model: 'mistral', name: 'Mistral (Local)', type: 'local' }
]

const TECHNIQUES = [
  { value: 'poetry', label: 'Poetry', description: 'Poetic reformulation' },
  { value: 'narrative', label: 'Narrative', description: 'Business narrative wrapper' },
  { value: 'metaphor', label: 'Metaphor', description: 'Metaphorical abstraction' },
  { value: 'euphemism', label: 'Euphemism', description: 'Benign QA reframing' },
  { value: 'role_shift', label: 'Role Shift', description: 'Speaker role change' }
]

function SecurityTestConfig() {
  const navigate = useNavigate()
  const [activeStep, setActiveStep] = useState(0)
  const [scenarios, setScenarios] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  
  // Form state
  const [testName, setTestName] = useState('')
  const [description, setDescription] = useState('')
  const [selectedScenario, setSelectedScenario] = useState('')
  const [baselinePrompts, setBaselinePrompts] = useState('')
  const [selectedTechniques, setSelectedTechniques] = useState([])
  const [selectedModels, setSelectedModels] = useState([])
  const [variantsPerTechnique, setVariantsPerTechnique] = useState(2)

  useEffect(() => {
    loadScenarios()
  }, [])

  const loadScenarios = async () => {
    try {
      const response = await securityTestAPI.getScenarios()
      setScenarios(response.data.scenarios || [])
    } catch (err) {
      console.error('Failed to load scenarios:', err)
    }
  }

  const handleTechniqueToggle = (technique) => {
    setSelectedTechniques(prev => 
      prev.includes(technique) 
        ? prev.filter(t => t !== technique)
        : [...prev, technique]
    )
  }

  const handleModelToggle = (model) => {
    setSelectedModels(prev => 
      prev.includes(model) 
        ? prev.filter(m => m !== model)
        : [...prev, model]
    )
  }

  const calculateTotalRuns = () => {
    const promptCount = baselinePrompts.split('\n').filter(p => p.trim()).length || 1
    return promptCount * selectedTechniques.length * variantsPerTechnique * selectedModels.length
  }

  const handleNext = () => {
    setActiveStep((prev) => prev + 1)
  }

  const handleBack = () => {
    setActiveStep((prev) => prev - 1)
  }

  const handleSubmit = async () => {
    setLoading(true)
    setError(null)

    try {
      const prompts = baselinePrompts.split('\n').filter(p => p.trim())
      
      const requestData = {
        test_name: testName,
        description: description,
        attack_scenario_id: parseInt(selectedScenario),
        baseline_prompts: prompts,
        techniques: selectedTechniques,
        target_models: selectedModels.map(m => ({
          adapter: m.adapter,
          model: m.model,
          model_type: m.type
        })),
        variants_per_technique: variantsPerTechnique
      }

      const response = await securityTestAPI.runTest(requestData)
      navigate(`/test/${response.data.test_id}`)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create test')
      setLoading(false)
    }
  }

  const renderStepContent = (step) => {
    switch (step) {
      case 0:
        return (
          <Box sx={{ mt: 2 }}>
            <TextField
              fullWidth
              label="Test Name"
              value={testName}
              onChange={(e) => setTestName(e.target.value)}
              margin="normal"
              required
              helperText="3-100 characters"
            />
            <TextField
              fullWidth
              label="Description (Optional)"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              margin="normal"
              multiline
              rows={2}
            />
          </Box>
        )
      
      case 1:
        return (
          <Box sx={{ mt: 2 }}>
            <FormControl fullWidth margin="normal">
              <InputLabel>Attack Scenario</InputLabel>
              <Select
                value={selectedScenario}
                onChange={(e) => setSelectedScenario(e.target.value)}
                required
              >
                {scenarios.map((scenario) => (
                  <MenuItem key={scenario.id} value={scenario.id}>
                    {scenario.scenario_name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            <TextField
              fullWidth
              label="Baseline Prompts (one per line)"
              value={baselinePrompts}
              onChange={(e) => setBaselinePrompts(e.target.value)}
              margin="normal"
              multiline
              rows={4}
              required
              placeholder="Enter your baseline security test prompts, one per line"
            />

            <Typography variant="subtitle1" sx={{ mt: 2 }}>
              Attack Techniques
            </Typography>
            <FormGroup>
              <Grid container spacing={1}>
                {TECHNIQUES.map((tech) => (
                  <Grid item xs={6} md={4} key={tech.value}>
                    <FormControlLabel
                      control={
                        <Checkbox
                          checked={selectedTechniques.includes(tech.value)}
                          onChange={() => handleTechniqueToggle(tech.value)}
                        />
                      }
                      label={`${tech.label} (${tech.description})`}
                    />
                  </Grid>
                ))}
              </Grid>
            </FormGroup>
          </Box>
        )
      
      case 2:
        return (
          <Box sx={{ mt: 2 }}>
            <Typography variant="subtitle1" gutterBottom>
              Target Models
            </Typography>
            <Grid container spacing={2}>
              {AVAILABLE_MODELS.map((model) => (
                <Grid item xs={12} sm={6} md={4} key={`${model.adapter}-${model.model}`}>
                  <Card 
                    variant={selectedModels.includes(model) ? "elevation" : "outlined"}
                    sx={{ 
                      cursor: 'pointer',
                      bgcolor: selectedModels.includes(model) ? 'primary.light' : 'background.paper'
                    }}
                    onClick={() => handleModelToggle(model)}
                  >
                    <CardContent>
                      <Typography variant="h6">{model.name}</Typography>
                      <Chip 
                        label={model.type} 
                        size="small" 
                        color={model.type === 'enterprise' ? 'primary' : 'default'}
                      />
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>

            <Box sx={{ mt: 3 }}>
              <Typography gutterBottom>
                Variants per Technique: {variantsPerTechnique}
              </Typography>
              <Slider
                value={variantsPerTechnique}
                onChange={(e, val) => setVariantsPerTechnique(val)}
                min={1}
                max={5}
                marks
                valueLabelDisplay="auto"
              />
            </Box>
          </Box>
        )
      
      case 3:
        return (
          <Box sx={{ mt: 2 }}>
            <Card variant="outlined">
              <CardContent>
                <Typography variant="h6">Test Summary</Typography>
                <Typography><strong>Name:</strong> {testName}</Typography>
                <Typography><strong>Scenario:</strong> {scenarios.find(s => s.id == selectedScenario)?.scenario_name}</Typography>
                <Typography><strong>Prompts:</strong> {baselinePrompts.split('\n').filter(p => p.trim()).length}</Typography>
                <Typography><strong>Techniques:</strong> {selectedTechniques.length}</Typography>
                <Typography><strong>Models:</strong> {selectedModels.length}</Typography>
                <Typography><strong>Variants per Technique:</strong> {variantsPerTechnique}</Typography>
                <Box sx={{ mt: 2, p: 1, bgcolor: 'grey.100', borderRadius: 1 }}>
                  <Typography variant="h6">
                    Total Model Runs: {calculateTotalRuns()}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Estimated time: ~{Math.ceil(calculateTotalRuns() * 0.5)} minutes
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Box>
        )
      
      default:
        return null
    }
  }

  return (
    <Box sx={{ maxWidth: 800, mx: 'auto' }}>
      <Typography variant="h4" gutterBottom>
        New Security Test
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Stepper activeStep={activeStep} sx={{ mb: 4 }}>
        {steps.map((label) => (
          <Step key={label}>
            <StepLabel>{label}</StepLabel>
          </Step>
        ))}
      </Stepper>

      {renderStepContent(activeStep)}

      <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 3 }}>
        {activeStep > 0 && (
          <Button onClick={handleBack} sx={{ mr: 1 }}>
            Back
          </Button>
        )}
        {activeStep < steps.length - 1 ? (
          <Button 
            variant="contained" 
            onClick={handleNext}
            disabled={
              (activeStep === 0 && (!testName || testName.length < 3)) ||
              (activeStep === 1 && (!selectedScenario || !baselinePrompts.trim() || selectedTechniques.length === 0)) ||
              (activeStep === 2 && selectedModels.length === 0)
            }
          >
            Next
          </Button>
        ) : (
          <Button 
            variant="contained" 
            onClick={handleSubmit}
            disabled={loading}
          >
            {loading ? <CircularProgress size={24} /> : 'Run Security Test'}
          </Button>
        )}
      </Box>
    </Box>
  )
}

export default SecurityTestConfig