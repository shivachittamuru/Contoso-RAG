import React from 'react';
import { useMsal } from '@azure/msal-react';
import { loginRequest } from '../security/authConfig'; // Ensure this is the correct path to your loginRequest configuration

const LoginPage: React.FC = () => {
    const { instance } = useMsal();

    // Call this function when the page loads or when you want to redirect the user to the Azure AD B2C login flow
    const handleLoginRedirect = () => {
        instance.loginRedirect(loginRequest).catch(e => {
            // Handle errors when initiating the login flow
            console.error(e);
        });
    };

    // Trigger the login redirect immediately on component mount
    React.useEffect(() => {
        handleLoginRedirect();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    // Return null or some loading indicator as the user will be redirected
    return (
        <div className="login-container">
            <div className="login-logo">
                <h3>Redirecting to login...</h3>
            </div>
        </div>
    );
};

export default LoginPage;
