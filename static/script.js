document.addEventListener('DOMContentLoaded', () => {
    // Prediction Elements
    const inputField = document.getElementById('problemStatement');
    const predictBtn = document.getElementById('predictBtn');
    const loadingDiv = document.getElementById('loading');
    const errorAlert = document.getElementById('errorMessage');
    const resultSection = document.getElementById('resultSection');

    const categoryValue = document.getElementById('categoryValue');
    const architectureValue = document.getElementById('architectureValue');
    const explanationValue = document.getElementById('explanationValue');
    const codeValue = document.getElementById('codeValue');
    const mermaidDiagram = document.getElementById('mermaidDiagram');

    // Nav Elements
    const showLoginBtn = document.getElementById('showLoginBtn');
    const showSignupBtn = document.getElementById('showSignupBtn');
    const logoutBtn = document.getElementById('logoutBtn');
    const showHistoryBtn = document.getElementById('showHistoryBtn');
    const userGreeting = document.getElementById('userGreeting');

    // Modals
    const authModal = document.getElementById('authModal');
    const historyModal = document.getElementById('historyModal');
    const closeAuthModal = document.getElementById('closeAuthModal');
    const closeHistoryModal = document.getElementById('closeHistoryModal');

    // Auth Elements
    const authTitle = document.getElementById('authTitle');
    const authError = document.getElementById('authError');
    const usernameInput = document.getElementById('usernameInput');
    const passwordInput = document.getElementById('passwordInput');
    const authSubmitBtn = document.getElementById('authSubmitBtn');
    const authSwitchText = document.getElementById('authSwitchText');

    const historyListContainer = document.getElementById('historyListContainer');

    let currentAuthMode = 'login'; // 'login' or 'signup'

    // Initialize logic
    checkStatus();

    if (typeof mermaid !== 'undefined') {
        mermaid.initialize({ startOnLoad: false, theme: 'default' });
    } else {
        console.warn("Mermaid is not defined. Ensure mermaid.min.js is loading correctly.");
    }

    // Event Listeners
    predictBtn.addEventListener('click', handlePrediction);
    inputField.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handlePrediction();
    });

    showLoginBtn.addEventListener('click', () => openAuthModal('login'));
    showSignupBtn.addEventListener('click', () => openAuthModal('signup'));
    logoutBtn.addEventListener('click', handleLogout);
    showHistoryBtn.addEventListener('click', handleShowHistory);

    closeAuthModal.addEventListener('click', () => authModal.classList.add('hidden'));
    closeHistoryModal.addEventListener('click', () => historyModal.classList.add('hidden'));

    authSubmitBtn.addEventListener('click', handleAuthSubmit);
    passwordInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleAuthSubmit();
    });

    // Dynamic event delegated to parent for switch link because we rewrite HTML sometimes
    authSwitchText.addEventListener('click', (e) => {
        if(e.target && e.target.id === 'authSwitchLink'){
            if (currentAuthMode === 'login') openAuthModal('signup');
            else openAuthModal('login');
        }
    });


    // API Integration Functions
    async function checkStatus() {
        try {
            const res = await fetch('/status');
            const data = await res.json();
            updateNavState(data.logged_in, data.username);
        } catch (e) {
            console.error("Failed to check status", e);
        }
    }

    function updateNavState(isLoggedIn, username) {
        if (isLoggedIn) {
            showLoginBtn.classList.add('hidden');
            showSignupBtn.classList.add('hidden');
            logoutBtn.classList.remove('hidden');
            showHistoryBtn.classList.remove('hidden');
            userGreeting.textContent = `Hello, ${username}`;
            userGreeting.classList.remove('hidden');
        } else {
            showLoginBtn.classList.remove('hidden');
            showSignupBtn.classList.remove('hidden');
            logoutBtn.classList.add('hidden');
            showHistoryBtn.classList.add('hidden');
            userGreeting.classList.add('hidden');
        }
    }

    function openAuthModal(mode) {
        currentAuthMode = mode;
        usernameInput.value = '';
        passwordInput.value = '';
        authError.classList.add('hidden');
        if (mode === 'login') {
            authTitle.textContent = 'Login';
            authSwitchText.innerHTML = 'Don\'t have an account? <span id="authSwitchLink" class="text-link">Sign Up</span>';
        } else {
            authTitle.textContent = 'Sign Up';
            authSwitchText.innerHTML = 'Already have an account? <span id="authSwitchLink" class="text-link">Login</span>';
        }
        authModal.classList.remove('hidden');
    }

    async function handleAuthSubmit() {
        const username = usernameInput.value.trim();
        const password = passwordInput.value.trim();

        if (!username || !password) {
            authError.textContent = "Please fill in all fields.";
            authError.classList.remove('hidden');
            return;
        }

        const endpoint = currentAuthMode === 'login' ? '/login' : '/signup';
        try {
            const res = await fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });
            const data = await res.json();

            if (!res.ok) throw new Error(data.error || "Authentication failed");

            authModal.classList.add('hidden');
            checkStatus(); // Refresh nav
        } catch (e) {
            authError.textContent = e.message;
            authError.classList.remove('hidden');
        }
    }

    async function handleLogout() {
        try {
            await fetch('/logout', { method: 'POST' });
            checkStatus();
        } catch (e) {
            console.error("Logout failed", e);
        }
    }

    async function handleShowHistory() {
        try {
            const res = await fetch('/history');
            const data = await res.json();
            
            if (!res.ok) {
                alert(data.error || "Failed to fetch history");
                return;
            }

            historyListContainer.innerHTML = '';
            if (data.length === 0) {
                historyListContainer.innerHTML = '<p style="color: var(--text-muted); text-align: center; padding: 1rem;">No queries found.</p>';
            } else {
                data.forEach(item => {
                    const div = document.createElement('div');
                    div.className = 'history-item';
                    div.innerHTML = `
                        <div class="history-header">
                            <span>ID: ${item.id}</span>
                            <span>${item.timestamp}</span>
                        </div>
                        <div class="history-query">"${item.input_text}"</div>
                        <div class="history-badges">
                            <span class="history-badge cat">${item.category.toUpperCase()}</span>
                            <span class="history-badge arch">${item.architecture}</span>
                        </div>
                    `;
                    // Clicking a history item re-populates input!
                    div.addEventListener('click', () => {
                        inputField.value = item.input_text;
                        historyModal.classList.add('hidden');
                        handlePrediction();
                    });
                    div.title = "Click to run this prediction again";
                    div.style.cursor = 'pointer';
                    historyListContainer.appendChild(div);
                });
            }
            historyModal.classList.remove('hidden');
        } catch (e) {
            console.error("History fetch error:", e);
        }
    }

    async function handlePrediction() {
        const text = inputField.value.trim();
        if (!text) {
            showError("Please enter a problem statement!");
            return;
        }

        hideError();
        resultSection.classList.add('hidden');
        loadingDiv.classList.remove('hidden');
        predictBtn.disabled = true;

        try {
            const response = await fetch('/predict', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ statement: text })
            });

            const data = await response.json();

            if (!response.ok) throw new Error(data.error || "Failed to predict");

            // Populate Data
            categoryValue.textContent = data.category || 'Unknown';
            architectureValue.textContent = data.architecture_type || 'Unknown';
            explanationValue.textContent = data.explanation || 'No explanation available.';
            codeValue.textContent = data.code_template || 'No code available.';

            // Render Mermaid Diagram
            if (data.diagram && typeof mermaid !== 'undefined') {
                mermaidDiagram.removeAttribute('data-processed');
                mermaidDiagram.innerHTML = data.diagram;

                try {
                    if (mermaid.run) {
                        await mermaid.run({ nodes: [mermaidDiagram] });
                    } else {
                        mermaid.init(undefined, mermaidDiagram);
                    }
                } catch (e) {
                    console.error("Mermaid Render Error:", e);
                    mermaidDiagram.innerHTML = "<p>Error rendering diagram. " + e.message + "</p>";
                }
            } else if (!data.diagram) {
                mermaidDiagram.innerHTML = "<p>No diagram available.</p>";
            } else {
                mermaidDiagram.innerHTML = "<p>Mermaid library not loaded.</p>";
            }

            loadingDiv.classList.add('hidden');
            resultSection.classList.remove('hidden');

        } catch (err) {
            showError("An error occurred: " + err.message);
            loadingDiv.classList.add('hidden');
        } finally {
            predictBtn.disabled = false;
        }
    }

    function showError(msg) {
        errorAlert.textContent = msg;
        errorAlert.classList.remove('hidden');
    }

    function hideError() {
        errorAlert.classList.add('hidden');
    }
});
