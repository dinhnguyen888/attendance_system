<template>
    <div class="app-container">
        <nav class="nav-bar">
            <router-link to="/register" class="nav-link"
                >Face Registration</router-link
            >
            <router-link to="/verify" class="nav-link"
                >Face Verification</router-link
            >
        </nav>
        <router-view></router-view>
    </div>
</template>

<style scoped>
.app-container {
    min-height: 100vh;
    padding: 20px;
    background: #f7fafc;
}

.nav-bar {
    display: flex;
    justify-content: center;
    gap: 20px;
    margin-bottom: 30px;
}

.nav-link {
    padding: 10px 20px;
    color: #4a5568;
    text-decoration: none;
    border-radius: 4px;
    transition: all 0.2s;
}

.nav-link:hover {
    background: #edf2f7;
}

.router-link-active {
    color: #4299e1;
    background: #ebf8ff;
}
</style>
