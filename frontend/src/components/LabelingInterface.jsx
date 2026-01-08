import React, { useState, useEffect } from 'react'
import axios from 'axios'
import Navigation from './Navigation'

export default function LabelingInterface() {
  const [currentItem, setCurrentItem] = useState(null)
  const [labelValue, setLabelValue] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [startTime, setStartTime] = useState(null)

  useEffect(() => {
    fetchNextItem()
  }, [])

  const fetchNextItem = async () => {
    setLoading(true)
    setError('')
    setSuccess('')
    setLabelValue('')

    try {
      const response = await axios.get('/api/data-items?unlabeled_only=true&limit=1')
      if (response.data.length > 0) {
        setCurrentItem(response.data[0])
        setStartTime(Date.now())
      } else {
        setError('No unlabeled items available')
      }
    } catch (err) {
      setError('Failed to load data item')
    } finally {
      setLoading(false)
    }
  }

  const submitLabel = async (e) => {
    e.preventDefault()
    if (!labelValue.trim()) return

    setLoading(true)
    setError('')

    const timeSpent = (Date.now() - startTime) / 1000

    try {
      const response = await axios.post('/api/labels', {
        data_item_id: currentItem.id,
        label_value: labelValue.trim(),
        confidence: 1.0,
        time_spent: timeSpent
      })

      if (response.data.consensus_reached) {
        setSuccess(
          `Label submitted! Consensus reached: ${response.data.consensus_label}`
        )
      } else {
        setSuccess('Label submitted successfully!')
      }

      setTimeout(() => {
        fetchNextItem()
      }, 2000)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to submit label')
    } finally {
      setLoading(false)
    }
  }

  const skipItem = () => {
    fetchNextItem()
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Navigation />

      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">Label Data</h1>

        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}

        {success && (
          <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded mb-4">
            {success}
          </div>
        )}

        {loading && !currentItem ? (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">Loading next item...</p>
          </div>
        ) : currentItem ? (
          <div className="bg-white rounded-lg shadow-lg p-8">
            <div className="mb-6">
              <div className="text-sm text-gray-600 mb-2">Item Type</div>
              <div className="text-lg font-semibold uppercase">{currentItem.item_type}</div>
            </div>

            <div className="mb-6">
              <div className="text-sm text-gray-600 mb-4">Data to Label</div>
              {currentItem.item_type === 'image' ? (
                <img
                  src={currentItem.data_url}
                  alt="Item to label"
                  className="max-w-full max-h-96 rounded-lg border-2 border-gray-200 mx-auto"
                />
              ) : currentItem.item_type === 'text' ? (
                <div className="bg-gray-50 p-6 rounded-lg border-2 border-gray-200">
                  <p className="text-gray-800">{currentItem.data_url}</p>
                </div>
              ) : (
                <div className="bg-gray-50 p-6 rounded-lg border-2 border-gray-200">
                  <a
                    href={currentItem.data_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:underline"
                  >
                    View Data
                  </a>
                </div>
              )}
            </div>

            <form onSubmit={submitLabel} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Your Label
                </label>
                <input
                  type="text"
                  value={labelValue}
                  onChange={(e) => setLabelValue(e.target.value)}
                  placeholder="Enter your label (e.g., cat, dog, positive, negative)"
                  className="w-full px-4 py-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  disabled={loading}
                  required
                />
                <p className="text-xs text-gray-500 mt-1">
                  Tip: Be accurate! Correct labels earn you LABD tokens, incorrect ones lose tokens.
                </p>
              </div>

              <div className="flex gap-4">
                <button
                  type="submit"
                  disabled={loading || !labelValue.trim()}
                  className="flex-1 bg-blue-600 text-white py-3 rounded-md hover:bg-blue-700 transition disabled:bg-gray-400"
                >
                  {loading ? 'Submitting...' : 'Submit Label'}
                </button>
                <button
                  type="button"
                  onClick={skipItem}
                  disabled={loading}
                  className="px-6 bg-gray-300 text-gray-700 py-3 rounded-md hover:bg-gray-400 transition"
                >
                  Skip
                </button>
              </div>
            </form>

            <div className="mt-6 p-4 bg-blue-50 rounded-lg">
              <div className="flex items-center justify-between text-sm">
                <div>
                  <span className="text-gray-600">Labels needed:</span>
                  <span className="ml-2 font-bold">{currentItem.required_labels}</span>
                </div>
                <div>
                  <span className="text-gray-600">Reward:</span>
                  <span className="ml-2 font-bold text-green-600">+10 LABD</span>
                </div>
                <div>
                  <span className="text-gray-600">Penalty:</span>
                  <span className="ml-2 font-bold text-red-600">-5 LABD</span>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="text-center py-12 bg-white rounded-lg shadow-lg">
            <p className="text-gray-600 text-lg">No items available to label</p>
            <button
              onClick={fetchNextItem}
              className="mt-4 bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700 transition"
            >
              Refresh
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
