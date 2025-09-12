import { createRouter, createWebHistory } from "vue-router";
import FaceRegistrationPage from "./pages/FaceRegistrationPage.vue";
import FaceVerificationPage from "./pages/FaceVerificationPage.vue";

const routes = [
    {
        path: "/",
        redirect: "/verify",
    },
    {
        path: "/register",
        name: "register",
        component: FaceRegistrationPage,
    },
    {
        path: "/verify",
        name: "verify",
        component: FaceVerificationPage,
    },
];

const router = createRouter({
    history: createWebHistory(),
    routes,
});

export default router;
