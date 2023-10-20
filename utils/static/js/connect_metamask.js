if (typeof web3 !== 'undefined') {
  const loginButton = document.getElementById('connect-metamask');

  loginButton.addEventListener('click', async () => {
    try {
      await window.ethereum.request({ method: 'eth_requestAccounts' });
      const web3 = new Web3(window.ethereum);
      const accounts = await web3.eth.getAccounts();
      const userAddress = accounts[0];

      // Create a new XMLHttpRequest object
      const xhr = new XMLHttpRequest();
      xhr.open('POST', '/authenticate', true);
      xhr.setRequestHeader('Content-Type', 'application/json;charset=UTF-8');

      // Create a JSON object with the user's Ethereum address
      const userData = { userAddress };

      // Send the Ethereum address as JSON in the request body
      xhr.send(JSON.stringify(userData));

      // Redirect the user after the request is sent
      xhr.onreadystatechange = function () {
        if (xhr.readyState === 4 && xhr.status === 200) {
          window.location.href = 'index.html';
          console.log(`Logged in with address: ${userAddress}`);
        }
      };
    } catch (error) {
      console.error('Error logging in with MetaMask:', error);
    }
  });
} else {
  console.error('MetaMask is not installed.');
}
