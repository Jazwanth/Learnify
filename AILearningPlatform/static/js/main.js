/**
 * Main JavaScript file for the e-learning platform
 */

// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // Handle course module selection
    const moduleItems = document.querySelectorAll('.module-item');
    const moduleContent = document.getElementById('module-content');
    const videoContainer = document.getElementById('video-container');
    const moduleTitle = document.getElementById('module-title');
    const moduleText = document.getElementById('module-text');
    const quizContainer = document.getElementById('quiz-container');
    
    if (moduleItems.length > 0 && moduleContent) {
        moduleItems.forEach(item => {
            item.addEventListener('click', function() {
                // Remove active class from all modules
                moduleItems.forEach(m => m.classList.remove('active'));
                
                // Add active class to selected module
                this.classList.add('active');
                
                // Get module data
                const moduleId = this.getAttribute('data-module-id');
                const title = this.getAttribute('data-title');
                const content = this.getAttribute('data-content');
                const videoUrl = this.getAttribute('data-video');
                const quizData = this.getAttribute('data-quiz');
                const courseId = this.getAttribute('data-course-id');
                
                // Update module content
                moduleTitle.textContent = title;
                moduleText.textContent = content;
                
                // Update video if available
                if (videoUrl && videoUrl !== 'null') {
                    videoContainer.innerHTML = `
                        <iframe width="100%" height="315" src="${videoUrl}" 
                        title="${title}" frameborder="0" 
                        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
                        allowfullscreen></iframe>
                    `;
                    videoContainer.style.display = 'block';
                } else {
                    videoContainer.style.display = 'none';
                }
                
                // Update quiz if available
                if (quizData && quizData !== 'null') {
                    try {
                        const quiz = JSON.parse(quizData);
                        renderQuiz(quiz, moduleId, courseId);
                        quizContainer.style.display = 'block';
                    } catch (e) {
                        console.error('Error parsing quiz data:', e);
                        quizContainer.style.display = 'none';
                    }
                } else {
                    quizContainer.style.display = 'none';
                }
                
                // Show module content
                moduleContent.style.display = 'block';
                
                // Update progress
                updateModuleProgress(courseId, moduleId);
            });
        });
        
        // Show first module by default
        if (moduleItems.length > 0) {
            moduleItems[0].click();
        }
    }
    
    // Course enrollment confirmation
    const enrollButtons = document.querySelectorAll('.enroll-button');
    
    if (enrollButtons.length > 0) {
        enrollButtons.forEach(button => {
            button.addEventListener('click', function(e) {
                if (!confirm('Do you want to enroll in this course?')) {
                    e.preventDefault();
                }
            });
        });
    }
});

/**
 * Render a quiz from quiz data
 * 
 * @param {Array} quizData - Array of quiz questions
 * @param {Number} moduleId - The module ID
 * @param {Number} courseId - The course ID
 */
function renderQuiz(quizData, moduleId, courseId) {
    const quizContainer = document.getElementById('quiz-container');
    
    if (!quizContainer) return;
    
    let quizHTML = '<h4 class="mb-4">Module Quiz</h4>';
    
    quizData.forEach((question, qIndex) => {
        quizHTML += `
            <div class="question" data-question-id="${qIndex}">
                <h5 class="mb-3">${qIndex + 1}. ${question.question}</h5>
                <div class="options">
        `;
        
        question.options.forEach((option, oIndex) => {
            quizHTML += `
                <div class="option" data-option-id="${oIndex}">
                    ${option}
                </div>
            `;
        });
        
        quizHTML += `
                </div>
            </div>
        `;
    });
    
    quizHTML += `
        <div class="mt-4">
            <button id="submit-quiz" class="btn btn-primary">Submit Answers</button>
            <div id="quiz-results" class="mt-3"></div>
        </div>
    `;
    
    quizContainer.innerHTML = quizHTML;
    
    // Add event listeners for option selection
    const options = quizContainer.querySelectorAll('.option');
    options.forEach(option => {
        option.addEventListener('click', function() {
            // Remove selected class from all options in this question
            const questionDiv = this.closest('.question');
            const questionOptions = questionDiv.querySelectorAll('.option');
            questionOptions.forEach(opt => opt.classList.remove('selected'));
            
            // Add selected class to this option
            this.classList.add('selected');
        });
    });
    
    // Add event listener for quiz submission
    const submitButton = document.getElementById('submit-quiz');
    submitButton.addEventListener('click', function() {
        // Collect user answers
        const userAnswers = [];
        const questions = quizContainer.querySelectorAll('.question');
        
        questions.forEach(question => {
            const selectedOption = question.querySelector('.option.selected');
            if (selectedOption) {
                userAnswers.push(parseInt(selectedOption.getAttribute('data-option-id')));
            } else {
                userAnswers.push(null);
            }
        });
        
        // Calculate score
        let score = 0;
        let total = quizData.length;
        
        userAnswers.forEach((answer, index) => {
            if (answer !== null && answer === quizData[index].answer) {
                score++;
            }
        });
        
        const percentage = Math.round((score / total) * 100);
        
        // Display results
        const resultsDiv = document.getElementById('quiz-results');
        resultsDiv.innerHTML = `
            <div class="alert ${percentage >= 70 ? 'alert-success' : 'alert-warning'}">
                You scored ${score} out of ${total} (${percentage}%)
            </div>
        `;
        
        // Highlight correct and incorrect answers
        questions.forEach((question, qIndex) => {
            const options = question.querySelectorAll('.option');
            const correctAnswer = quizData[qIndex].answer;
            const userAnswer = userAnswers[qIndex];
            
            options.forEach((option, oIndex) => {
                if (oIndex === correctAnswer) {
                    option.classList.add('correct');
                } else if (oIndex === userAnswer && userAnswer !== correctAnswer) {
                    option.classList.add('incorrect');
                }
            });
        });
        
        // Disable further selections
        options.forEach(option => {
            option.style.pointerEvents = 'none';
        });
        
        // Update progress with quiz score
        updateModuleProgress(courseId, moduleId, percentage);
    });
}

/**
 * Update module progress
 * 
 * @param {Number} courseId - The course ID
 * @param {Number} moduleId - The module ID
 * @param {Number} quizScore - Optional quiz score
 */
function updateModuleProgress(courseId, moduleId, quizScore = null) {
    // Get course and calculate progress
    const moduleItems = document.querySelectorAll('.module-item');
    const totalModules = moduleItems.length;
    const currentIndex = Array.from(moduleItems).findIndex(m => 
        m.getAttribute('data-module-id') == moduleId
    );
    
    // Calculate completion percentage based on current module
    let completion = Math.round(((currentIndex + 1) / totalModules) * 100);
    
    // Update progress bar if it exists
    const progressBar = document.getElementById('course-progress-bar');
    if (progressBar) {
        progressBar.style.width = `${completion}%`;
        progressBar.setAttribute('aria-valuenow', completion);
        progressBar.textContent = `${completion}%`;
    }
    
    // Send progress update to server
    fetch('/update_progress', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            course_id: courseId,
            module_id: moduleId,
            completion: completion,
            quiz_score: quizScore
        })
    })
    .then(response => response.json())
    .then(data => {
        console.log('Progress updated:', data);
    })
    .catch(error => {
        console.error('Error updating progress:', error);
    });
}
