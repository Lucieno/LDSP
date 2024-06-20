module.exports = {
  networks: {
    development: {
      host: "127.0.0.1",
      port: 8545,
      network_id: "*" // Match any network id
    }
  },
compilers: {
  solc: {
      version: "^0.7.6", // A version or constraint - Ex. "^0.5.0"
                         // Can also be set to "native" to use a native solc
      settings: {
        optimizer: {
          enabled: true,
          runs: 1,   // Optimize for how many times you intend to run the code
          // constantOptimizer: true,
        },
        // evmVersion: "byzantium" // Default: "istanbul"
      }
    }
  }
};
