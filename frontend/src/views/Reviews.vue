<template>
  <div class="reviews-container">
    <!-- Back Button -->
    <div class="back-button-container">
      <button class="back-button" @click="goToFiles" title="Back to Files">
        <span class="back-icon">←</span>
        <span class="back-text">Back to Files</span>
      </button>
    </div>
    
    <div class="reviews-header">
      <h1>
        <span class="clickable-icon" @click="goToFiles" title="Back to Files">📋</span>
        My Reviews
      </h1>
      <p>Manage document review requests assigned to you</p>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="loading">
      <div class="loading-spinner"></div>
      <p>Loading reviews...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="error-message">
      <span class="icon">⚠️</span>
      {{ error }}
      <button @click="loadReviews" class="retry-btn">Retry</button>
    </div>

    <!-- Reviews List -->
    <div v-else class="reviews-content">
      <div v-if="reviews.length === 0" class="no-reviews">
        <span class="icon">📝</span>
        <h3>No reviews assigned</h3>
        <p>You don't have any pending document reviews at this time.</p>
        <router-link to="/files" class="btn btn-primary">
          <span class="icon">📁</span>
          Go to Files
        </router-link>
      </div>

      <div v-else class="reviews-list">
        <div 
          v-for="review in reviews" 
          :key="review.id" 
          class="review-card"
          :class="{ 'review-completed': review.status !== 'pending' }"
        >
          <div class="review-header">
            <div class="review-info">
              <h3>{{ review.filename }}</h3>
              <div class="review-meta">
                <span class="requester">
                  <span class="icon">👤</span>
                  Requested by: {{ review.requester }}
                </span>
                <span class="request-date">
                  <span class="icon">📅</span>
                  {{ formatDate(review.requested_at) }}
                </span>
              </div>
            </div>
            <span class="review-status" :class="review.status">
              {{ getStatusText(review.status) }}
            </span>
          </div>

          <div class="review-body">
            <div class="review-actions" v-if="review.status === 'pending'">
              <button
                v-if="review.has_comparison"
                class="btn btn-info"
                @click="openComparisonModal(review)"
                :disabled="submitting"
              >
                <span class="icon">🔍</span>
                View Changes
              </button>
              <button
                class="btn btn-success"
                @click="openReviewModal(review, 'approved')"
                :disabled="submitting"
              >
                <span class="icon">✅</span>
                Approve
              </button>
              <button
                class="btn btn-danger"
                @click="openReviewModal(review, 'rejected')"
                :disabled="submitting"
              >
                <span class="icon">❌</span>
                Reject
              </button>
              <a
                :href="`${baseURL}/download/${review.file_id}`"
                target="_blank"
                class="btn btn-secondary"
              >
                <span class="icon">📥</span>
                Download
              </a>
            </div>
            
            <div v-else class="review-completed-info">
              <div class="completion-date">
                <span class="icon">📅</span>
                Reviewed on: {{ formatDate(review.reviewed_at) }}
              </div>
              <div v-if="review.comments" class="review-comments">
                <h4>Comments:</h4>
                <p>{{ review.comments }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Review Decision Modal -->
    <div v-if="showReviewModal" class="modal-overlay" @click="closeReviewModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>
            <span class="icon">{{ currentDecision === 'approved' ? '✅' : '❌' }}</span>
            {{ currentDecision === 'approved' ? 'Approve' : 'Reject' }} Review
          </h3>
          <button class="modal-close" @click="closeReviewModal">×</button>
        </div>
        
        <div class="modal-body">
          <div class="review-details">
            <p><strong>File:</strong> {{ selectedReview?.filename }}</p>
            <p><strong>Requester:</strong> {{ selectedReview?.requester }}</p>
            <p><strong>Decision:</strong> 
              <span :class="currentDecision">
                {{ currentDecision === 'approved' ? 'Approve' : 'Reject' }}
              </span>
            </p>
          </div>
          
          <div class="comments-section">
            <label for="review-comments">Comments (optional):</label>
            <textarea
              id="review-comments"
              v-model="reviewComments"
              placeholder="Add any comments about your decision..."
              rows="4"
              class="comments-textarea"
            ></textarea>
          </div>
        </div>

        <div class="modal-footer">
          <button class="btn btn-secondary" @click="closeReviewModal" :disabled="submitting">
            Cancel
          </button>
          <button 
            class="btn"
            :class="currentDecision === 'approved' ? 'btn-success' : 'btn-danger'"
            @click="submitReview" 
            :disabled="submitting"
          >
            <span v-if="submitting" class="icon">⏳</span>
            <span v-else class="icon">{{ currentDecision === 'approved' ? '✅' : '❌' }}</span>
            {{ submitting ? 'Submitting...' : (currentDecision === 'approved' ? 'Approve' : 'Reject') }}
          </button>
        </div>
      </div>
    </div>

    <!-- Comparison Modal -->
    <div v-if="showComparisonModal" class="modal-overlay" @click="closeComparisonModal">
      <div class="modal-content comparison-modal" @click.stop>
        <div class="modal-header">
          <h3>
            <span class="icon">🔍</span>
            Content Comparison - {{ comparisonData?.filename }}
          </h3>
          <button class="modal-close" @click="closeComparisonModal">×</button>
        </div>
        
        <div class="modal-body">
          <div v-if="loadingComparison" class="loading-comparison">
            <div class="loading-spinner"></div>
            <p>Loading comparison...</p>
          </div>
          
          <div v-else-if="comparisonError" class="error-message">
            <span class="icon">⚠️</span>
            {{ comparisonError }}
          </div>
          
          <div v-else-if="comparisonData" class="comparison-container">
            <div class="comparison-info">
              <p><strong>Requester:</strong> {{ comparisonData.requester }}</p>
              <p><strong>Requested:</strong> {{ formatDate(comparisonData.requested_at) }}</p>
              <p v-if="comparisonData.original_version">
                <strong>Comparing:</strong> 
                Version {{ comparisonData.original_version || 'Original' }} → Version {{ comparisonData.modified_version }}
              </p>
              <div class="view-toggle">
                <div class="toggle-note">
                  <span class="icon">💡</span>
                  <small>Use "Formatted View" to see bold text, images, and other formatting</small>
                </div>
                <label class="toggle-label">
                  <input 
                    type="checkbox" 
                    v-model="showHtmlView" 
                    class="toggle-checkbox"
                  />
                  <span class="toggle-text">{{ showHtmlView ? 'Formatted View' : 'Raw Text View' }}</span>
                </label>
              </div>
            </div>
            
            <div class="comparison-panels">
              <div class="comparison-panel">
                <h4>
                  <span class="icon">📄</span>
                  Original Content
                  <span v-if="comparisonData.original_version" class="version-badge">
                    v{{ comparisonData.original_version }}
                  </span>
                </h4>
                <div class="content-display">
                  <div 
                    v-if="showHtmlView && comparisonData.original_content" 
                    class="html-content"
                    v-html="comparisonData.original_content"
                  ></div>
                  <pre 
                    v-else-if="!showHtmlView && comparisonData.original_content"
                    class="plain-text-content"
                  >{{ stripHtmlTags(comparisonData.original_content) }}</pre>
                  <div v-else class="empty-content">
                    <span class="icon">📝</span>
                    <p>No original content</p>
                  </div>
                </div>
              </div>
              
              <div class="comparison-panel">
                <h4>
                  <span class="icon">✏️</span>
                  Modified Content
                  <span class="version-badge modified">
                    v{{ comparisonData.modified_version }}
                  </span>
                </h4>
                <div class="content-display">
                  <div 
                    v-if="showHtmlView && comparisonData.modified_content" 
                    class="html-content"
                    v-html="comparisonData.modified_content"
                  ></div>
                  <pre 
                    v-else-if="!showHtmlView && comparisonData.modified_content"
                    class="plain-text-content"
                  >{{ stripHtmlTags(comparisonData.modified_content) }}</pre>
                  <div v-else class="empty-content">
                    <span class="icon">📝</span>
                    <p>No modified content</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="modal-footer">
          <button class="btn btn-secondary" @click="closeComparisonModal">
            Close
          </button>
          <button 
            v-if="selectedReviewForComparison"
            class="btn btn-success" 
            @click="approveFromComparison"
            :disabled="submitting"
          >
            <span v-if="submitting" class="icon">⏳</span>
            <span v-else class="icon">✅</span>
            Approve Changes
          </button>
          <button 
            v-if="selectedReviewForComparison"
            class="btn btn-danger" 
            @click="rejectFromComparison"
            :disabled="submitting"
          >
            <span v-if="submitting" class="icon">⏳</span>
            <span v-else class="icon">❌</span>
            Reject Changes
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

const router = useRouter()
const reviews = ref([])
const loading = ref(true)
const error = ref(null)
const submitting = ref(false)
const showReviewModal = ref(false)
const selectedReview = ref(null)
const currentDecision = ref(null)
const reviewComments = ref('')
const showComparisonModal = ref(false)
const comparisonData = ref(null)
const loadingComparison = ref(true)
const comparisonError = ref(null)
const selectedReviewForComparison = ref(null)
const showHtmlView = ref(true)

const baseURL = axios.defaults.baseURL

async function loadReviews() {
  loading.value = true
  error.value = null
  
  try {
    const response = await axios.get('/my-reviews', { withCredentials: true })
    reviews.value = response.data
  } catch (err) {
    console.error('Error loading reviews:', err)
    error.value = err.response?.data?.error || 'Failed to load reviews'
  } finally {
    loading.value = false
  }
}

function openReviewModal(review, decision) {
  selectedReview.value = review
  currentDecision.value = decision
  reviewComments.value = ''
  showReviewModal.value = true
}

function closeReviewModal() {
  showReviewModal.value = false
  selectedReview.value = null
  currentDecision.value = null
  reviewComments.value = ''
}

async function submitReview() {
  if (!selectedReview.value || !currentDecision.value) return
  
  submitting.value = true
  
  try {
    await axios.post(`/review/${selectedReview.value.id}`, {
      decision: currentDecision.value,
      comments: reviewComments.value
    }, { withCredentials: true })
    
    // Update the review in the local state
    const reviewIndex = reviews.value.findIndex(r => r.id === selectedReview.value.id)
    if (reviewIndex !== -1) {
      reviews.value[reviewIndex].status = currentDecision.value
      reviews.value[reviewIndex].comments = reviewComments.value
      reviews.value[reviewIndex].reviewed_at = new Date().toISOString()
    }
    
    closeReviewModal()
  } catch (err) {
    console.error('Error submitting review:', err)
    error.value = err.response?.data?.error || 'Failed to submit review'
  } finally {
    submitting.value = false
  }
}

function getStatusText(status) {
  switch (status) {
    case 'pending': return 'Pending Review'
    case 'approved': return 'Approved'
    case 'rejected': return 'Rejected'
    case 'cancelled': return 'Cancelled'
    default: return status
  }
}

function formatDate(dateString) {
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function goToFiles() {
  router.push('/files')
}

async function openComparisonModal(review) {
  selectedReviewForComparison.value = review
  showComparisonModal.value = true
  loadingComparison.value = true
  comparisonError.value = null
  
  try {
    const response = await axios.get(`/review-comparison/${review.id}`, { withCredentials: true })
    comparisonData.value = response.data
  } catch (err) {
    console.error('Error loading comparison:', err)
    comparisonError.value = err.response?.data?.error || 'Failed to load comparison'
  } finally {
    loadingComparison.value = false
  }
}

function closeComparisonModal() {
  showComparisonModal.value = false
  selectedReviewForComparison.value = null
  comparisonData.value = null
  comparisonError.value = null
  loadingComparison.value = true
}

async function approveFromComparison() {
  if (!selectedReviewForComparison.value) return
  
  submitting.value = true
  
  try {
    await axios.post(`/review/${selectedReviewForComparison.value.id}`, {
      decision: 'approved',
      comments: 'Approved after reviewing changes'
    }, { withCredentials: true })
    
    // Update the review in the local state
    const reviewIndex = reviews.value.findIndex(r => r.id === selectedReviewForComparison.value.id)
    if (reviewIndex !== -1) {
      reviews.value[reviewIndex].status = 'approved'
      reviews.value[reviewIndex].comments = 'Approved after reviewing changes'
      reviews.value[reviewIndex].reviewed_at = new Date().toISOString()
    }
    
    closeComparisonModal()
  } catch (err) {
    console.error('Error approving from comparison:', err)
    comparisonError.value = err.response?.data?.error || 'Failed to approve from comparison'
  } finally {
    submitting.value = false
  }
}

async function rejectFromComparison() {
  if (!selectedReviewForComparison.value) return
  
  submitting.value = true
  
  try {
    await axios.post(`/review/${selectedReviewForComparison.value.id}`, {
      decision: 'rejected',
      comments: 'Rejected after reviewing changes'
    }, { withCredentials: true })
    
    // Update the review in the local state
    const reviewIndex = reviews.value.findIndex(r => r.id === selectedReviewForComparison.value.id)
    if (reviewIndex !== -1) {
      reviews.value[reviewIndex].status = 'rejected'
      reviews.value[reviewIndex].comments = 'Rejected after reviewing changes'
      reviews.value[reviewIndex].reviewed_at = new Date().toISOString()
    }
    
    closeComparisonModal()
  } catch (err) {
    console.error('Error rejecting from comparison:', err)
    comparisonError.value = err.response?.data?.error || 'Failed to reject from comparison'
  } finally {
    submitting.value = false
  }
}

function stripHtmlTags(html) {
  return html.replace(/<[^>]+>/g, '').replace(/\s+/g, ' ').trim()
}

onMounted(() => {
  loadReviews()
})
</script>

<style scoped>
.reviews-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
}

.back-button-container {
  margin-bottom: 1rem;
}

.back-button {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  background: linear-gradient(135deg, #4299e1 0%, #3182ce 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 2px 4px rgba(66, 153, 225, 0.2);
}

.back-button:hover {
  background: linear-gradient(135deg, #3182ce 0%, #2c5aa0 100%);
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(66, 153, 225, 0.3);
}

.back-button:active {
  transform: translateY(0);
  box-shadow: 0 2px 4px rgba(66, 153, 225, 0.2);
}

.back-icon {
  font-size: 1.2rem;
  font-weight: bold;
}

.back-text {
  font-weight: 500;
}

.reviews-header {
  text-align: center;
  margin-bottom: 2rem;
}

.reviews-header h1 {
  color: #2d3748;
  margin-bottom: 0.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}

.reviews-header p {
  color: #718096;
  font-size: 1.1rem;
}

.loading {
  text-align: center;
  padding: 3rem;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #e2e8f0;
  border-top: 4px solid #4299e1;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 1rem;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error-message {
  background: #fed7d7;
  color: #c53030;
  padding: 1rem;
  border-radius: 8px;
  text-align: center;
  margin: 2rem 0;
}

.retry-btn {
  background: #c53030;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  margin-left: 1rem;
  cursor: pointer;
}

.no-reviews {
  text-align: center;
  padding: 4rem 2rem;
  background: #f7fafc;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
}

.no-reviews .icon {
  font-size: 3rem;
  display: block;
  margin-bottom: 1rem;
}

.no-reviews h3 {
  color: #2d3748;
  margin-bottom: 0.5rem;
}

.no-reviews p {
  color: #718096;
  margin-bottom: 2rem;
}

.reviews-list {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.review-card {
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  transition: all 0.2s ease;
}

.review-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  transform: translateY(-1px);
}

.review-completed {
  opacity: 0.8;
  border-left: 4px solid #48bb78;
}

.review-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1rem;
}

.review-info h3 {
  margin: 0 0 0.5rem 0;
  color: #2d3748;
}

.review-meta {
  display: flex;
  gap: 1rem;
  font-size: 0.9rem;
  color: #718096;
}

.review-status {
  padding: 0.5rem 1rem;
  border-radius: 20px;
  font-size: 0.8rem;
  font-weight: 600;
  text-transform: uppercase;
}

.review-status.pending {
  background: #fef3c7;
  color: #92400e;
}

.review-status.approved {
  background: #d4edda;
  color: #155724;
}

.review-status.rejected {
  background: #f8d7da;
  color: #721c24;
}

.review-status.cancelled {
  background: #e2e8f0;
  color: #4a5568;
}

.review-actions {
  display: flex;
  gap: 1rem;
  margin-top: 1rem;
}

.review-completed-info {
  background: #f7fafc;
  padding: 1rem;
  border-radius: 8px;
  margin-top: 1rem;
}

.completion-date {
  font-size: 0.9rem;
  color: #718096;
  margin-bottom: 0.5rem;
}

.review-comments h4 {
  margin: 0 0 0.5rem 0;
  color: #2d3748;
  font-size: 0.9rem;
}

.review-comments p {
  margin: 0;
  color: #4a5568;
  font-style: italic;
  background: white;
  padding: 0.75rem;
  border-radius: 4px;
}

.btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 6px;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  text-decoration: none;
  transition: all 0.2s ease;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary {
  background: #4299e1;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #3182ce;
}

.btn-success {
  background: #48bb78;
  color: white;
}

.btn-success:hover:not(:disabled) {
  background: #38a169;
}

.btn-danger {
  background: #f56565;
  color: white;
}

.btn-danger:hover:not(:disabled) {
  background: #e53e3e;
}

.btn-secondary {
  background: #a0aec0;
  color: white;
}

.btn-secondary:hover:not(:disabled) {
  background: #718096;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
  padding: 20px;
}

.modal-content {
  background: white;
  border-radius: 12px;
  width: 90%;
  max-width: 500px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
  display: flex;
  flex-direction: column;
  max-height: 100%;
}

.modal-header {
  padding: 1.5rem;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-header h3 {
  margin: 0;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.modal-close {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #718096;
}

.modal-body {
  padding: 1.5rem;
}

.review-details {
  background: #f7fafc;
  padding: 1rem;
  border-radius: 8px;
  margin-bottom: 1rem;
}

.review-details p {
  margin: 0.5rem 0;
}

.review-details .approved {
  color: #38a169;
  font-weight: 600;
}

.review-details .rejected {
  color: #e53e3e;
  font-weight: 600;
}

.comments-section label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
  color: #2d3748;
}

.comments-textarea {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-family: inherit;
  resize: vertical;
  min-height: 100px;
}

.comments-textarea:focus {
  outline: none;
  border-color: #4299e1;
  box-shadow: 0 0 0 3px rgba(66, 153, 225, 0.1);
}

.modal-footer {
  padding: 1rem 1.5rem;
  border-top: 1px solid #e2e8f0;
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  background: white;
  border-radius: 0 0 12px 12px;
  flex-shrink: 0;
}

.icon {
  display: inline-block;
}

.clickable-icon {
  cursor: pointer;
  transition: all 0.2s ease;
  padding: 0.25rem;
  border-radius: 6px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.clickable-icon:hover {
  background-color: rgba(66, 153, 225, 0.1);
  transform: scale(1.1);
}

.loading-comparison {
  text-align: center;
  padding: 3rem;
}

.comparison-container {
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  transition: all 0.2s ease;
}

.comparison-info {
  margin-bottom: 1.5rem;
}

.comparison-info p {
  margin: 0.5rem 0;
}

.comparison-panels {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
}

.comparison-panel {
  flex: 1;
  background: #f7fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 1rem;
  min-height: calc(100vh - 350px);
  display: flex;
  flex-direction: column;
}

.comparison-panel h4 {
  margin: 0 0 1rem 0;
  color: #2d3748;
  font-size: 1rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.content-display {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: calc(100vh - 400px);
}

.content-display .html-content,
.content-display .plain-text-content {
  flex: 1;
  max-height: calc(100vh - 400px);
}

.content-display pre {
  margin: 0;
  padding: 1rem;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 0.9rem;
  line-height: 1.5;
  white-space: pre-wrap;
  word-wrap: break-word;
  background: white;
  color: #2d3748;
  max-height: calc(100vh - 400px);
  overflow-y: auto;
}

.empty-content {
  text-align: center;
  padding: 4rem 2rem;
  background: #f7fafc;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
}

.empty-content .icon {
  font-size: 3rem;
  display: block;
  margin-bottom: 1rem;
}

.empty-content p {
  color: #718096;
  margin-bottom: 2rem;
}

.version-badge {
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.8rem;
  font-weight: 600;
  text-transform: uppercase;
  background: #e2e8f0;
  color: #4a5568;
}

.version-badge.modified {
  background: #fef3c7;
  color: #92400e;
}

.comparison-modal {
  max-width: none;
  width: calc(100vw - 40px);
  max-height: calc(100vh - 40px);
  height: calc(100vh - 40px);
}

.comparison-modal .modal-body {
  max-height: calc(100vh - 200px);
  overflow-y: auto;
  padding: 1rem;
}

.view-toggle {
  margin-top: 1rem;
  text-align: center;
}

.toggle-note {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
  color: #718096;
  font-size: 0.85rem;
}

.toggle-note .icon {
  font-size: 1rem;
}

.toggle-label {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 500;
}

.toggle-checkbox {
  position: relative;
  width: 50px;
  height: 24px;
  appearance: none;
  background: #e2e8f0;
  border-radius: 12px;
  outline: none;
  cursor: pointer;
  transition: all 0.3s ease;
}

.toggle-checkbox:checked {
  background: #4299e1;
}

.toggle-checkbox::before {
  content: '';
  position: absolute;
  top: 2px;
  left: 2px;
  width: 20px;
  height: 20px;
  background: white;
  border-radius: 50%;
  transition: all 0.3s ease;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.toggle-checkbox:checked::before {
  transform: translateX(26px);
}

.toggle-text {
  color: #4a5568;
  user-select: none;
}

.html-content {
  padding: 1rem;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  overflow-y: auto;
  max-height: calc(100vh - 400px);
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  line-height: 1.6;
}

.html-content h1, .html-content h2, .html-content h3, 
.html-content h4, .html-content h5, .html-content h6 {
  margin: 1rem 0 0.5rem 0;
  color: #2d3748;
  font-weight: bold;
}

.html-content p {
  margin: 0.5rem 0;
  color: #4a5568;
}

.html-content strong, .html-content b {
  font-weight: bold;
  color: #2d3748;
}

.html-content em, .html-content i {
  font-style: italic;
}

.html-content u {
  text-decoration: underline;
}

.html-content s, .html-content strike {
  text-decoration: line-through;
}

.html-content ul, .html-content ol {
  margin: 0.5rem 0;
  padding-left: 1.5rem;
}

.html-content li {
  margin: 0.25rem 0;
}

.html-content blockquote {
  border-left: 4px solid #e2e8f0;
  padding-left: 1rem;
  margin: 1rem 0;
  font-style: italic;
  color: #718096;
  background: #f7fafc;
}

.html-content code {
  background: #f7fafc;
  padding: 0.125rem 0.25rem;
  border-radius: 3px;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 0.875rem;
  color: #e53e3e;
}

.html-content pre {
  background: #f7fafc;
  padding: 1rem;
  border-radius: 6px;
  overflow-x: auto;
  margin: 1rem 0;
  border: 1px solid #e2e8f0;
}

.html-content img {
  max-width: 100%;
  height: auto;
  border-radius: 8px;
  margin: 1rem 0;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  border: 2px solid #e2e8f0;
  display: block;
  cursor: pointer;
  transition: all 0.3s ease;
}

.html-content img:hover {
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.2);
  transform: scale(1.02);
}

.html-content a {
  color: #4299e1;
  text-decoration: underline;
}

.html-content a:hover {
  color: #3182ce;
}

/* Quill editor specific styles */
.html-content .ql-align-center {
  text-align: center;
}

.html-content .ql-align-right {
  text-align: right;
}

.html-content .ql-align-justify {
  text-align: justify;
}

.html-content .ql-indent-1 {
  padding-left: 3em;
}

.html-content .ql-indent-2 {
  padding-left: 6em;
}

.html-content .ql-indent-3 {
  padding-left: 9em;
}

/* Handle empty paragraphs from Quill */
.html-content p:empty::before {
  content: '\00a0'; /* Non-breaking space */
}

.html-content br {
  line-height: 1.6;
}

.plain-text-content {
  margin: 0;
  padding: 1rem;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 0.9rem;
  line-height: 1.5;
  white-space: pre-wrap;
  word-wrap: break-word;
  background: white;
  color: #2d3748;
  max-height: calc(100vh - 400px);
  overflow-y: auto;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
}

@media (max-width: 768px) {
  .reviews-container {
    padding: 1rem;
  }
  
  .review-header {
    flex-direction: column;
    gap: 1rem;
  }
  
  .review-meta {
    flex-direction: column;
    gap: 0.5rem;
  }
  
  .review-actions {
    flex-direction: column;
  }
  
  .modal-content {
    width: 95%;
    margin: 1rem;
  }
  
  .comparison-panels {
    grid-template-columns: 1fr;
    gap: 1rem;
  }
  
  .comparison-modal {
    width: 99%;
    margin: 0.25rem;
    max-height: 98vh;
    height: 95vh;
  }
  
  .comparison-modal .modal-body {
    max-height: 80vh;
    padding: 0.75rem;
  }
  
  .comparison-panel {
    min-height: 350px;
  }
  
  .content-display {
    min-height: 300px;
  }
  
  .content-display .html-content,
  .content-display .plain-text-content {
    max-height: 300px;
  }
  
  .content-display pre {
    font-size: 0.8rem;
    max-height: 300px;
  }
  
  .html-content {
    max-height: 300px;
  }
  
  .plain-text-content {
    max-height: 300px;
  }
}
</style> 