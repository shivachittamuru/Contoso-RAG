import React from 'react';
import { useState } from 'react'
import reactLogo from '../assets/react.svg'
import viteLogo from '/vite.svg'
import { useAuth } from '../security/AuthContext';

export const Default = () => {
  const [count, setCount] = useState<number>(0);
  const [message, setMessage] = useState<string>('');
//   const [username, setUsername] = useState<string>('');
//   const [password, setPassword] = useState<string>('');
  //const [authToken, setAuthToken] = useState<string>('');
  const { userToken } = useAuth();

  console.log('entered Default.tsx');

  const handleSubmit = async (event: { preventDefault: () => void; }) => {
    event.preventDefault();
   // const tokenData = await login(username, password);
   // setAuthToken(tokenData.access_token);
   //setAuthToken(userToken?.token);
    console.log(`Token is ${userToken?.token}`);
    
    sayHello(userToken?.token);
  };

  const sayHello = async (token: string | undefined) => {
    try {
      console.log('Calling FastAPI');
      const response = await fetch('/user/hello', {
        headers: {
          Accept: 'application/json',
          Authorization: `Bearer ${token}`
        }
      });
  
      console.log(`Got response ${response}`);
      const data = await response.json();
      console.log(data); 
      setMessage(data.message);
    } catch (error) {
      console.error('There was an error!', error);
    }
  };

//   const login = async (username: string, password: string) => {
//     try {
//       const response = await fetch('http://localhost:8000/auth/token', {
//         method: 'POST',
//         headers: {
//           'Content-Type': 'application/x-www-form-urlencoded'
//         },
//         body: new URLSearchParams({
//           username: username,
//           password: password
//         })
//       });
  
//       if (!response.ok) {
//         throw new Error(`HTTP error! Status: ${response.status}`);
//       }
  
//       const data = await response.json();
//       console.log(data); 
//       return data;
//     } catch (error) {
//       console.error('Login error:', error);
//     }
//   }

  return (
    <>
      <div>
        <a href="https://vitejs.dev" target="_blank" rel="noopener">
          <img src={viteLogo} className="logo" alt="Vite logo" />
        </a>
        <a href="https://react.dev" target="_blank" rel="noopener">
          <img src={reactLogo} className="logo react" alt="React logo" />
        </a>
      </div>
      <h1>Vite + React</h1>
      <div className="card">
        <button onClick={() => setCount((count) => count + 1)}>
          count is {count}
        </button>
        <p>
          Edit <code>src/App.tsx</code> and save to test HMR
        </p>
      </div>
      <p className="read-the-docs">
        Click on the Vite and React logos to learn more
      </p>
      <div>
        The message is {message}
      </div>
      <form onSubmit={handleSubmit}>
      {/* <input 
        type="text" 
        value={username} 
        onChange={(e) => setUsername(e.target.value)} 
        placeholder="Username" 
      />
      <input 
        type="password" 
        value={password} 
        onChange={(e) => setPassword(e.target.value)} 
        placeholder="Password" 
      /> */}
      <button type="submit">Say Hello</button>
    </form>
    </>
  )
};

export default Default;