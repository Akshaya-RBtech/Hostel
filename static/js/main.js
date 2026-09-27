// Common UI Logic for Smart Hostel Food Waste Management System

function switchTab(tab) {
    // Hide all tab contents
    document.querySelectorAll('.tab-content').forEach(el => el.classList.add('hidden'));
    
    // Reset all tab button styles
    document.querySelectorAll('[id^="tab-"]').forEach(el => {
        el.classList.remove('bg-white', 'shadow-sm', 'text-indigo-600');
        el.classList.add('text-gray-500');
    });

    // Show the selected tab content
    const content = document.getElementById('content-' + tab);
    if (content) {
        content.classList.remove('hidden');
    }

    // Highlight the selected tab button
    const button = document.getElementById('tab-' + tab);
    if (button) {
        button.classList.add('bg-white', 'shadow-sm', 'text-indigo-600');
        button.classList.remove('text-gray-500');
    }

    // Special handling for analytics tab
    if (tab === 'analytics' && typeof loadAnalytics === 'function') {
        loadAnalytics();
    }
}
