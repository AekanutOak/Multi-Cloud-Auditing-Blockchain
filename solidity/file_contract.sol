// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

// one file on contract

contract FileContract {
    mapping(address => string) private ACL;
    mapping(address => string) private addressToKey;

    struct LogData {
        address invoker;
        uint256 timestamp;
        string eventDesc;
    }

    string[] public blockTag;
    LogData[] private fileLog;
    address[] private userList;

    string private fileID;
    string private filename;
    address private ownerAddress;
    string private description;
    uint256 private createdDate;
    uint256 private lastUpdate;
    uint256 private fileSizeInByte;
    uint256 private numberOfBlock;

    uint256[] private challenge;
    bytes32[] private response;

    // When deploy the contract, initialize some variables first
    constructor(

        // Block tag is sign(hash(block),SK); will perform off-chain for saving gas cost and improve speed
        string[] memory _blockTag,
        string memory _ID,
        string memory _filename,
        string memory _desc,
        string memory _key,
        uint256 _size
    ) {
        require(bytes(_filename).length > 0, "Filename cannot be blank");
        require(bytes(_key).length > 0, "You must provide a key; otherwise, the file will be unable to be decrypted");
        require(_size > 0, "Make sure you put the right size of the file");
        require(_blockTag.length > 0, "Make sure you put the right block list");

        ACL[msg.sender] = "rw";
        addressToKey[msg.sender] = _key;
        fileLog.push(LogData({
            invoker: msg.sender,
            timestamp: block.timestamp,
            eventDesc: "Initially upload file"
        }));

        userList.push(msg.sender);
        fileID = _ID;
        filename = _filename;
        numberOfBlock = _blockTag.length;
        fileSizeInByte = _size;
        ownerAddress = msg.sender;
        description = _desc;
        createdDate = block.timestamp;
        lastUpdate = block.timestamp;
        blockTag = _blockTag;
    }

    // Get the file metadata such as name, size, number of block, etc.
    function get_file_metadata() public view returns (string memory, string memory, address, string memory, uint256, uint256, uint256, uint256) {
        require(bytes(ACL[msg.sender]).length != 0, "You don't have permission to access this file");
        return (fileID, filename, ownerAddress, description, createdDate, lastUpdate, fileSizeInByte, numberOfBlock);
    }

    // Retrieve tag of all blocks
    function get_block_tag() public view returns (string[] memory) {
        require(bytes(ACL[msg.sender]).length != 0, "You don't have permission to access this file");
        return blockTag;
    }

    // Retrieve all log data
    function get_log_data() public view returns (LogData[] memory) {
        require(msg.sender == ownerAddress, "Only owner can see the log");
        return fileLog;
    }

    // Assign ACL to both existing user or non-existing user in the system
    // If user does not in the system before, simply assign ACL and add to userList array
    function assign_ACL(address[] memory users, string[] memory permissions, string[] memory keys) public {
        require(msg.sender == ownerAddress, "You don't have permission to assign ACL");
        require(users.length == permissions.length, "Number of permissions and users do not match");

        for (uint256 i = 0; i < users.length; i++) {
            // assign the ACL
            ACL[users[i]] = permissions[i];
            addressToKey[users[i]] = keys[i];
            // Check if user does not in the array before, just add it
            if (!isUserInList(users[i])) {
                userList.push(users[i]);
            }

            fileLog.push(LogData({
                invoker: msg.sender,
                timestamp: block.timestamp,
                eventDesc: string(abi.encodePacked("Assign permission ", permissions[i], " to address ", addressToString(users[i])))
            }));
        }
    }

    // Remove the user from userList, and set ACL to ""
    // No need to generate new key because, ACL and require will prevent user from accessing the data
    // Will implement regenerate key in future because this function will take a lot of resource from both user and blockchain
    function revoke_users(address[] memory users) public {
        require(msg.sender == ownerAddress, "You don't have permission to revoke users");
        for (uint256 i = 0; i < users.length; i++) {
            ACL[users[i]] = "";
            addressToKey[users[i]] = "";
            removeUserFromList(users[i]);

            fileLog.push(LogData({
                invoker: msg.sender,
                timestamp: block.timestamp,
                eventDesc: string(abi.encodePacked("Revoke user address ", addressToString(users[i])))
            }));
        }
    }

    // Check if user in userList
    function isUserInList(address user) internal view returns (bool) {
        for (uint256 i = 0; i < userList.length; i++) {
            if (userList[i] == user) {
                return true;
            }
        }
        return false;
    }

    // remove the user from userList
    function removeUserFromList(address user) internal {
        for (uint256 i = 0; i < userList.length; i++) {
            if (userList[i] == user) {
                userList[i] = userList[userList.length - 1];
                userList.pop();
                break;
            }
        }
    }

    // convert solidity address to string
    function addressToString(address addr) internal pure returns (string memory) {
        bytes32 value = bytes32(uint256(uint160(addr)));
        bytes memory alphabet = "0123456789abcdef";

        bytes memory str = new bytes(42);
        str[0] = "0";
        str[1] = "x";

        for (uint256 i = 0; i < 20; i++) {
            str[2 + i * 2] = alphabet[uint8(value[i + 12] >> 4)];
            str[3 + i * 2] = alphabet[uint8(value[i + 12] & 0x0f)];
        }

        return string(str);
    }

    // for data owner to randomly submit the set of block index to challenge the CSP
    function submit_challenge(uint256[] memory blockIndexList) public {
        require(msg.sender == ownerAddress, "Only owner can perform a challenge");

        for (uint256 i = 0; i < blockIndexList.length; i++) {
            require(blockIndexList[i] >= 0 && blockIndexList[i] < numberOfBlock, "Invalid block index");
        }

        fileLog.push(LogData({
            invoker: msg.sender,
            timestamp: block.timestamp,
            eventDesc: "Challenge is submitted"
        }));

        challenge = blockIndexList;
    }

    function get_key() public returns(string memory){
        require(bytes(ACL[msg.sender]).length != 0, "You don't have permission to access this file");
        fileLog.push(LogData({
                invoker: msg.sender,
                timestamp: block.timestamp,
                eventDesc: string(abi.encodePacked("User ", addressToString(msg.sender)," retrieve file"))
        }));
        return addressToKey[msg.sender];
    }

    // for CSP to get the challenge index of blocks
    function get_challenge() public view returns (uint256[] memory) {
        require(isUserInList(msg.sender), "You don't have permission to see the challenge");
        return challenge;
    }

    // for CSP to response to challenge by submit the list of raw data of block
    // The verification process will be performed off-chain
    // solidity don't support encrypt/decrypt
    // sign and verify the signature in solidity is cumbersome
    function response_to_challenge(string[] memory _blockList) public {
        require(isUserInList(msg.sender), "You don't have permission to respond");
        require(_blockList.length == challenge.length, "Number of responses must match the challenge");

        bytes32[] memory temp_hash = new bytes32[](_blockList.length);
        for (uint256 i = 0; i < _blockList.length; i++) {
            temp_hash[i] = sha256(abi.encodePacked(_blockList[i]));
        }

        fileLog.push(LogData({
            invoker: msg.sender,
            timestamp: block.timestamp,
            eventDesc: "Response to challenge"
        }));

        response = temp_hash;
    }

    // for data owner to get the response from CSP and verify them off-chain
    function get_response() public view returns (bytes32[] memory) {
        require(msg.sender == ownerAddress, "Only the owner can see the response to challenge");
        return response;
    }

    // To retrieve a specific set of block tag instead of all tag
    function get_set_of_tag(uint256[] memory BlockIndex) public view returns (string[] memory) {
        require(msg.sender == ownerAddress, "Only the owner can get the block tag");
        string[] memory temp = new string[](BlockIndex.length);

        for (uint256 i = 0; i < BlockIndex.length; i++) {
            require(BlockIndex[i] >= 0 && BlockIndex[i] < numberOfBlock, "Invalid block index");
            temp[i] = blockTag[BlockIndex[i]];
        }

        return temp;
    }

    // To generate custom log data
    function custom_log(string memory customLog) public {
        require(isUserInList(msg.sender), "You don't have permission to log anything");
        fileLog.push(LogData({
            invoker: msg.sender,
            timestamp: block.timestamp,
            eventDesc: customLog
        }));
    }

    function get_owner_address() public view returns(address){
        return ownerAddress;
    }

    function get_ACL(address userAddress) public view returns(string memory){
        return ACL[userAddress];
    }

    function get_all_ACL() public view returns (address[] memory, string[] memory) {
    require(msg.sender == ownerAddress, "Only the owner can see the access control list");
    string[] memory ACLList = new string[](userList.length);

    for (uint i = 0; i < userList.length; i++) {
        ACLList[i] = ACL[userList[i]];
    }

    return (userList, ACLList);
    }
}
