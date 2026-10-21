
import React, { useState } from 'react'
import { Card } from '../components/ui'
import Layout from '../layouts/MainLayout'

const Settings: React.FC = () => {
  const [thresholds, setThresholds] = useState({
    highConfidence: 90,
    reviewThreshold: 75,
    unknownThreshold: 75,
  })

  const [livenessSettings, setLivenessSettings] = useState({
    enabled: true,
    spoofThreshold: 0.5,
  })

  const [mlSettings, setMLSettings] = useState({
    model: 'logistic_regression',
    autoTrain: false,
  })

  const saveThresholds = () => {
    alert('Confidence thresholds saved (demo only)')
  }

  const saveLivenessSettings = () => {
    alert('Liveness settings saved (demo only)')
  }

  const saveMLSettings = () => {
    alert('ML settings saved (demo only)')
  }

  return (
    <Layout>
      <h2>Settings</h2>

      <div className="settings-container">
        <Card>
          <h3>Recognition Thresholds</h3>
          <p>Configure confidence thresholds for face recognition.</p>

          <table>
            <thead>
              <tr>
                <th>Threshold Type</th>
                <th>Value</th>
                <th>Description</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>High Confidence</td>
                <td>
                  <input
                    type="number"
                    min="0"
                    max="100"
                    value={thresholds.highConfidence}
                    onChange={(e) =>
                      setThresholds({
                        ...thresholds,
                        highConfidence: Number(e.target.value),
                      })
                    }
                  />
                  {thresholds.highConfidence}%
                </td>
                <td>90% or above → High confidence</td>
              </tr>

              <tr>
                <td>Review Threshold</td>
                <td>
                  <input
                    type="number"
                    min="0"
                    max="100"
                    value={thresholds.reviewThreshold}
                    onChange={(e) =>
                      setThresholds({
                        ...thresholds,
                        reviewThreshold: Number(e.target.value),
                      })
                    }
                  />
                  {thresholds.reviewThreshold}%
                </td>
                <td>75–89% → Review</td>
              </tr>

              <tr>
                <td>Unknown Threshold</td>
                <td>
                  <input
                    type="number"
                    min="0"
                    max="100"
                    value={thresholds.unknownThreshold}
                    onChange={(e) =>
                      setThresholds({
                        ...thresholds,
                        unknownThreshold: Number(e.target.value),
                      })
                    }
                  />
                  {thresholds.unknownThreshold}%
                </td>
                <td>&lt; 75% → Unknown</td>
              </tr>
            </tbody>
          </table>

          <button onClick={saveThresholds} className="btn-primary">
            Save Thresholds
          </button>
        </Card>

        <Card>
          <h3>Liveness Detection</h3>

          <label>
            <input
              type="checkbox"
              checked={livenessSettings.enabled}
              onChange={(e) =>
                setLivenessSettings({
                  ...livenessSettings,
                  enabled: e.target.checked,
                })
              }
            />
            Enable liveness/anti-spoofing check
          </label>

          <p>
            Liveness is an additional verification layer and is not
            guaranteed to stop every attack.
          </p>

          <button onClick={saveLivenessSettings} className="btn-primary">
            Save Liveness Settings
          </button>
        </Card>

        <Card>
          <h3>Machine Learning</h3>
          <p>Attendance risk prediction model configuration.</p>

          <select
            value={mlSettings.model}
            onChange={(e) =>
              setMLSettings({
                ...mlSettings,
                model: e.target.value,
              })
            }
          >
            <option value="logistic_regression">Logistic Regression</option>
            <option value="random_forest">Random Forest</option>
            <option value="xgboost">XGBoost</option>
          </select>

          <label>
            <input
              type="checkbox"
              checked={mlSettings.autoTrain}
              onChange={(e) =>
                setMLSettings({
                  ...mlSettings,
                  autoTrain: e.target.checked,
                })
              }
            />
            Auto-train on new data
          </label>

          <button onClick={saveMLSettings} className="btn-primary">
            Save ML Settings
          </button>
        </Card>
      </div>
    </Layout>
  )
}

export default Settings
