import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useIsAuthenticated } from '@azure/msal-react';

const PostLogin = () => {
  const navigate = useNavigate();
  const isAuthenticated = useIsAuthenticated();

  useEffect(() => {
    // If the user is authenticated, redirect to the chat interface
    if (isAuthenticated) {
      navigate('/app/chat');
    }
    // Otherwise, send them to the login page
    else {
      navigate('/login');
    }
  }, [isAuthenticated, navigate]);

  // Render nothing or a loading indicator until the redirect is complete
  return null;
};

export default PostLogin;
