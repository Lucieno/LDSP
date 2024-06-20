var Migrations = artifacts.require("./Migrations.sol");
var LDSP = artifacts.require("./LDSP.sol");

module.exports = function(deployer) {
  deployer.deploy(Migrations);
  deployer.deploy(LDSP);
};
