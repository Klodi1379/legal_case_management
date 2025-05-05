// AI Services JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Model selection in forms
    const modelSelectors = document.querySelectorAll('.model-selector');
    if (modelSelectors.length > 0) {
        modelSelectors.forEach(selector => {
            selector.addEventListener('change', function() {
                const modelId = this.value;
                const modelCards = document.querySelectorAll('.model-card');
                
                modelCards.forEach(card => {
                    if (card.dataset.modelId === modelId) {
                        card.classList.add('active');
                    } else {
                        card.classList.remove('active');
                    }
                });
            });
        });
    }
    
    // Document analysis form
    const analysisForm = document.getElementById('analysisForm');
    if (analysisForm) {
        analysisForm.addEventListener('submit', function() {
            const submitButton = this.querySelector('button[type="submit"]');
            const loadingSpinner = document.getElementById('loadingSpinner');
            
            submitButton.disabled = true;
            loadingSpinner.classList.remove('d-none');
        });
    }
    
    // Legal research form
    const researchForm = document.getElementById('researchForm');
    if (researchForm) {
        researchForm.addEventListener('submit', function() {
            const submitButton = this.querySelector('button[type="submit"]');
            const loadingSpinner = document.getElementById('researchLoadingSpinner');
            
            submitButton.disabled = true;
            loadingSpinner.classList.remove('d-none');
        });
    }
    
    // Document generation form
    const generationForm = document.getElementById('documentGenerationForm');
    if (generationForm) {
        generationForm.addEventListener('submit', function() {
            const submitButton = this.querySelector('button[type="submit"]');
            const loadingSpinner = document.getElementById('generationLoadingSpinner');
            
            submitButton.disabled = true;
            loadingSpinner.classList.remove('d-none');
        });
        
        // Template buttons
        const templateButtons = document.querySelectorAll('.template-button');
        templateButtons.forEach(button => {
            button.addEventListener('click', function() {
                const templateId = this.dataset.templateId;
                useTemplate(templateId);
            });
        });
    }
    
    // Copy to clipboard functionality
    const copyButtons = document.querySelectorAll('.copy-button');
    if (copyButtons.length > 0) {
        copyButtons.forEach(button => {
            button.addEventListener('click', function() {
                const textToCopy = document.getElementById(this.dataset.target).textContent;
                navigator.clipboard.writeText(textToCopy).then(() => {
                    // Show success message
                    const originalText = this.innerHTML;
                    this.innerHTML = '<i class="fas fa-check"></i> Copied!';
                    
                    setTimeout(() => {
                        this.innerHTML = originalText;
                    }, 2000);
                });
            });
        });
    }
    
    // Analysis type selection
    const analysisTypeSelect = document.getElementById('analysisType');
    if (analysisTypeSelect) {
        analysisTypeSelect.addEventListener('change', function() {
            const selectedType = this.value;
            const customInstructions = document.getElementById('customInstructionsContainer');
            
            // Show custom instructions for certain analysis types
            if (selectedType === 'legal_analysis' || selectedType === 'custom') {
                customInstructions.classList.remove('d-none');
            } else {
                customInstructions.classList.add('d-none');
            }
        });
    }
    
    // Document preview toggle
    const previewToggle = document.getElementById('previewToggle');
    if (previewToggle) {
        previewToggle.addEventListener('click', function() {
            const previewContainer = document.getElementById('documentPreview');
            if (previewContainer.classList.contains('d-none')) {
                previewContainer.classList.remove('d-none');
                this.innerHTML = '<i class="fas fa-eye-slash me-1"></i> Hide Document';
            } else {
                previewContainer.classList.add('d-none');
                this.innerHTML = '<i class="fas fa-eye me-1"></i> Show Document';
            }
        });
    }
    
    // Example search buttons
    const exampleSearchButtons = document.querySelectorAll('.example-search');
    if (exampleSearchButtons.length > 0) {
        exampleSearchButtons.forEach(button => {
            button.addEventListener('click', function() {
                const searchInput = document.querySelector('input[name="query"]');
                searchInput.value = this.textContent.trim();
                
                // Focus on the search input
                searchInput.focus();
            });
        });
    }
});

// Function to use document generation templates
function useTemplate(templateId) {
    const documentTypeSelect = document.getElementById('documentType');
    const contentInput = document.getElementById('contentInput');
    
    switch (templateId) {
        case 'motion_dismiss':
            documentTypeSelect.value = 'motion';
            contentInput.value = 'Create a motion to dismiss based on [specify grounds]. The case involves [describe case briefly]. Include standard legal language for this jurisdiction and cite relevant precedents.';
            break;
        case 'client_agreement':
            documentTypeSelect.value = 'contract';
            contentInput.value = 'Create a client engagement agreement for legal services. Include sections on scope of representation, fees and billing, client responsibilities, termination, and confidentiality.';
            break;
        case 'settlement':
            documentTypeSelect.value = 'contract';
            contentInput.value = 'Draft a settlement agreement for [describe dispute]. Include terms for payment, release of claims, confidentiality, and non-disparagement.';
            break;
        case 'demand_letter':
            documentTypeSelect.value = 'letter';
            contentInput.value = 'Write a demand letter regarding [describe issue]. Request [specific remedy] within [timeframe] to avoid further legal action.';
            break;
    }
    
    // Focus on the content input for editing
    contentInput.focus();
}
