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
}

.modal-content {
  background: white;
  border-radius: 12px;
  width: 90%;
  max-width: 500px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
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
}
</style> 