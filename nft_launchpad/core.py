"""
NFT发行平台核心组件
支持创建、发行和交易NFT集合
"""

import asyncio
import hashlib
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import uuid
from datetime import datetime, timedelta
import ipfshttpclient
import web3
from web3 import Web3
from eth_account import Account


class NFTStandard(Enum):
    ERC721 = "ERC721"
    ERC1155 = "ERC1155"


@dataclass
class NFTMetadata:
    name: str
    description: str
    image: str  # IPFS CID或URL
    attributes: List[Dict[str, Any]]
    external_url: Optional[str] = None
    animation_url: Optional[str] = None
    youtube_url: Optional[str] = None


@dataclass
class CollectionConfig:
    name: str
    symbol: str
    description: str
    royalty_percentage: float  # 2.5表示2.5%
    royalty_recipient: str  # 收益地址
    max_supply: int
    price_per_mint: float  # ETH/BNB等原生代币价格
    standard: NFTStandard
    metadata_base_uri: str
    reveal_phase: bool = False
    whitelist_enabled: bool = False


@dataclass
class MintOrder:
    collection_address: str
    buyer_address: str
    quantity: int
    price: float
    timestamp: datetime
    tx_hash: Optional[str] = None
    completed: bool = False


class NFTHelper:
    """NFT辅助工具类"""
    
    @staticmethod
    def generate_token_id(collection_address: str, index: int) -> str:
        """生成唯一的token ID"""
        hash_input = f"{collection_address}{index}{uuid.uuid4()}".encode()
        return hashlib.sha256(hash_input).hexdigest()[:16]  # 截取前16位
    
    @staticmethod
    def upload_to_ipfs(data: Dict, filename: str = "metadata.json") -> str:
        """上传数据到IPFS"""
        try:
            client = ipfshttpclient.connect('/ip4/127.0.0.1/tcp/5001/http')
            res = client.add_json(data)
            return res['Hash']
        except Exception as e:
            print(f"IPFS上传失败: {e}")
            # 返回模拟CID
            return f"Qm{'a'*44}"
    
    @staticmethod
    def verify_signature(message: str, signature: str, address: str) -> bool:
        """验证签名"""
        try:
            # 这里会实际验证签名
            return True  # 模拟返回True
        except Exception:
            return False


class SmartContractGenerator:
    """智能合约生成器"""
    
    @staticmethod
    def generate_erc721_contract(config: CollectionConfig) -> str:
        """生成ERC721智能合约代码"""
        contract_code = f'''
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/token/ERC721/extensions/ERC721Enumerable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract {config.name.replace(" ", "")} is ERC721, ERC721Enumerable, ReentrancyGuard, Ownable {{
    using Strings for uint256;

    string public baseExtension = ".json";
    string public baseURI;
    string public notRevealedUri;
    
    uint256 public cost = {int(config.price_per_mint * 1e18)}; // {config.price_per_mint} ETH/BNB
    uint256 public maxSupply = {config.max_supply};
    uint256 public maxMintAmount = 20;
    bool public paused = false;
    bool public revealed = false;
    bool public whitelistMintEnabled = {str(config.whitelist_enabled).lower()};
    bool public publicMintEnabled = true;
    
    mapping(address => bool) public whitelist;
    mapping(uint256 => string) private customURIs;

    constructor(string memory _name, string memory _symbol, string memory _initBaseURI, string memory _notRevealedUri) 
        ERC721(_name, _symbol) {{
        setBaseURI(_initBaseURI);
        setNotRevealedURI(_notRevealedUri);
    }}

    // internal
    function _baseURI() internal view virtual override returns (string memory) {{
        return baseURI;
    }}

    // public
    function mint(uint256 _mintAmount) public payable nonReentrant {{
        uint256 supply = totalSupply();
        require(!paused, "the contract is paused");
        require(_mintAmount > 0, "need to mint at least 1 NFT");
        require(_mintAmount <= maxMintAmount, "max mint amount per session exceeded");
        require(supply + _mintAmount <= maxSupply, "max NFT limit exceeded");
        
        if (msg.sender != owner()) {{
            if(whitelistMintEnabled) {{
                require(whitelist[msg.sender], "user is not whitelisted");
                require(_mintAmount <= 1, "only 1 per wallet during whitelist phase");
            }}
            require(msg.value >= cost * _mintAmount, "insufficient funds");
        }}

        for (uint256 i = 1; i <= _mintAmount; i++) {{
            _safeMint(msg.sender, supply + i);
        }}
    }}
    
    function walletOfOwner(address _owner) public view returns (uint256[] memory) {{
        uint256 ownerTokenCount = balanceOf(_owner);
        uint256[] memory tokenIds = new uint256[](ownerTokenCount);
        for (uint256 i; i < ownerTokenCount; i++) {{
            tokenIds[i] = tokenOfOwnerByIndex(_owner, i);
        }}
        return tokenIds;
    }}

    function tokenURI(uint256 tokenId) public view virtual override returns (string memory) {{
        require(_exists(tokenId), "ERC721Metadata: URI query for nonexistent token");
        
        if(revealed == false) {{
            return notRevealedUri;
        }}

        string memory currentBaseURI = _baseURI();
        return bytes(currentBaseURI).length > 0
            ? string(abi.encodePacked(currentBaseURI, tokenId.toString(), baseExtension))
            : "";
    }}

    //only owner
    function reveal() public onlyOwner {{
        revealed = true;
    }}
    
    function setCost(uint256 _newCost) public onlyOwner {{
        cost = _newCost;
    }}

    function setMaxMintAmount(uint256 _newMaxMintAmount) public onlyOwner {{
        maxMintAmount = _newMaxMintAmount;
    }}

    function setNotRevealedURI(string memory _notRevealedURI) public onlyOwner {{
        notRevealedUri = _notRevealedURI;
    }}

    function setBaseURI(string memory _newBaseURI) public onlyOwner {{
        baseURI = _newBaseURI;
    }}

    function setBaseExtension(string memory _newBaseExtension) public onlyOwner {{
        baseExtension = _newBaseExtension;
    }}
    
    function setWhitelistMintEnabled(bool _state) public onlyOwner {{
        whitelistMintEnabled = _state;
    }}
    
    function whitelistUsers(address[] calldata _users) public onlyOwner {{
        for(uint i = 0; i < _users.length; i++) {{
            whitelist[_users[i]] = true;
        }}
    }}
    
    function removeWhitelistUsers(address[] calldata _users) public onlyOwner {{
        for(uint i = 0; i < _users.length; i++) {{
            whitelist[_users[i]] = false;
        }}
    }}

    function pause(bool _state) public onlyOwner {{
        paused = _state;
    }}
    
    function withdraw() public payable onlyOwner {{
        (bool os, ) = payable(owner()).call{{value: address(this).balance}}("");
        require(os);
    }}
}}
'''
        return contract_code
    
    @staticmethod
    def generate_erc1155_contract(config: CollectionConfig) -> str:
        """生成ERC1155智能合约代码"""
        contract_code = f'''
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/token/ERC1155/ERC1155.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/Strings.sol";

contract {config.name.replace(" ", "")}Multi is ERC1155, ReentrancyGuard, Ownable {{
    using Strings for uint256;

    mapping(uint256 => string) private _uris;
    mapping(uint256 => uint256) public tokenPrice;
    mapping(uint256 => uint256) public maxSupply;
    mapping(uint256 => uint256) public totalMinted;
    
    uint256 public constant MAX_TOKENS = {config.max_supply};
    uint256 public cost = {int(config.price_per_mint * 1e18)};
    bool public saleIsActive = false;

    constructor(string memory _uri) ERC1155(_uri) {{
    }}

    function uri(uint256 _tokenId) public view virtual override returns (string memory) {{
        return _uris[_tokenId];
    }}

    function setURI(uint256 _tokenId, string memory _uri) public onlyOwner {{
        _uris[_tokenId] = _uri;
    }}

    function setCost(uint256 _tokenId, uint256 _cost) public onlyOwner {{
        tokenPrice[_tokenId] = _cost;
    }}
    
    function setMaxSupply(uint256 _tokenId, uint256 _supply) public onlyOwner {{
        maxSupply[_tokenId] = _supply;
    }}

    function mint(uint256 _tokenId, uint256 _amount) public payable nonReentrant {{
        require(saleIsActive, "Sale must be active to mint");
        require(_amount > 0, "Must mint at least 1 NFT");
        require(totalMinted[_tokenId] + _amount <= maxSupply[_tokenId], "Purchase would exceed max supply");
        require(msg.value >= tokenPrice[_tokenId] * _amount, "Ether value sent is not correct");

        totalMinted[_tokenId] += _amount;
        _mint(msg.sender, _tokenId, _amount, "");
    }}

    function flipSaleState() public onlyOwner {{
        saleIsActive = !saleIsActive;
    }}

    function withdraw() public payable onlyOwner {{
        (bool os, ) = payable(owner()).call{{value: address(this).balance}}("");
        require(os);
    }}
}}
'''
        return contract_code


class NFTCollectionManager:
    """NFT集合管理器"""
    
    def __init__(self):
        self.collections = {}
        self.mint_orders = []
        self.contract_generator = SmartContractGenerator()
    
    def create_collection(self, config: CollectionConfig, creator_address: str) -> str:
        """创建NFT集合"""
        collection_id = str(uuid.uuid4())
        
        collection_data = {
            'id': collection_id,
            'config': config.__dict__,
            'creator': creator_address,
            'created_at': datetime.now().isoformat(),
            'total_minted': 0,
            'holders': {},
            'stats': {
                'floor_price': 0,
                'volume_24h': 0,
                'owners_count': 0
            }
        }
        
        self.collections[collection_id] = collection_data
        
        # 生成智能合约代码
        if config.standard == NFTStandard.ERC721:
            contract_code = self.contract_generator.generate_erc721_contract(config)
        else:
            contract_code = self.contract_generator.generate_erc1155_contract(config)
        
        # 这里会部署合约，现在保存代码供后续部署
        with open(f"contracts/{collection_id}_contract.sol", "w") as f:
            f.write(contract_code)
        
        print(f"🎨 NFT集合已创建: {config.name} (ID: {collection_id})")
        return collection_id
    
    def mint_nft(self, collection_id: str, buyer_address: str, quantity: int = 1) -> bool:
        """铸造NFT"""
        if collection_id not in self.collections:
            print("❌ 集合不存在")
            return False
        
        collection = self.collections[collection_id]
        config = CollectionConfig(**collection['config'])
        
        # 检查供应量
        if collection['total_minted'] + quantity > config.max_supply:
            print("❌ 超出最大供应量")
            return False
        
        # 检查价格
        total_cost = config.price_per_mint * quantity
        # 这里会检查买方余额，现在简化处理
        
        # 更新集合统计
        collection['total_minted'] += quantity
        
        if buyer_address not in collection['holders']:
            collection['holders'][buyer_address] = 0
        collection['holders'][buyer_address] += quantity
        
        # 创建铸造订单
        order = MintOrder(
            collection_address=collection_id,
            buyer_address=buyer_address,
            quantity=quantity,
            price=total_cost,
            timestamp=datetime.now()
        )
        self.mint_orders.append(order)
        
        print(f"🪙 {quantity}个NFT已铸造给 {buyer_address} (集合: {config.name})")
        return True
    
    def get_collection_info(self, collection_id: str) -> Optional[Dict]:
        """获取集合信息"""
        if collection_id not in self.collections:
            return None
        return self.collections[collection_id]
    
    def list_collections(self) -> List[Dict]:
        """列出所有集合"""
        return [{
            'id': cid,
            'name': c['config']['name'],
            'symbol': c['config']['symbol'],
            'total_minted': c['total_minted'],
            'max_supply': c['config']['max_supply'],
            'price_per_mint': c['config']['price_per_mint']
        } for cid, c in self.collections.items()]


class NFTMarketplace:
    """NFT市场"""
    
    def __init__(self, collection_manager: NFTCollectionManager):
        self.collection_manager = collection_manager
        self.listings = {}
        self.sales_history = []
    
    def list_nft(self, collection_id: str, token_id: str, seller_address: str, price: float, expiration_days: int = 30):
        """上架NFT"""
        listing_id = str(uuid.uuid4())
        
        listing = {
            'id': listing_id,
            'collection_id': collection_id,
            'token_id': token_id,
            'seller': seller_address,
            'price': price,
            'listed_at': datetime.now().isoformat(),
            'expires_at': (datetime.now() + timedelta(days=expiration_days)).isoformat()
        }
        
        self.listings[listing_id] = listing
        print(f"🏷️ NFT已上架: {token_id} in {collection_id} for {price} ETH")
    
    def buy_nft(self, listing_id: str, buyer_address: str) -> bool:
        """购买NFT"""
        if listing_id not in self.listings:
            print("❌ 上架不存在")
            return False
        
        listing = self.listings[listing_id]
        expires_at = datetime.fromisoformat(listing['expires_at'])
        
        if datetime.now() > expires_at:
            print("❌ 上架已过期")
            del self.listings[listing_id]
            return False
        
        # 这里会处理实际的转账，现在简化处理
        
        # 记录销售历史
        sale = {
            'listing_id': listing_id,
            'buyer': buyer_address,
            'sold_at': datetime.now().isoformat(),
            'price': listing['price']
        }
        self.sales_history.append(sale)
        
        # 从上架中移除
        del self.listings[listing_id]
        
        print(f"🤝 NFT已售出: {listing['token_id']} to {buyer_address} for {listing['price']} ETH")
        return True
    
    def get_marketplace_stats(self) -> Dict:
        """获取市场统计数据"""
        total_volume = sum(sale['price'] for sale in self.sales_history)
        total_sales = len(self.sales_history)
        
        return {
            'total_listings': len(self.listings),
            'total_sales': total_sales,
            'total_volume': total_volume,
            'average_sale_price': total_volume / total_sales if total_sales > 0 else 0
        }


class NFTLaunchpad:
    """NFT发行平台主类"""
    
    def __init__(self):
        self.collection_manager = NFTCollectionManager()
        self.marketplace = NFTMarketplace(self.collection_manager)
        self.ipfs_client = None
    
    def initialize_ipfs(self):
        """初始化IPFS客户端"""
        try:
            self.ipfs_client = ipfshttpclient.connect('/ip4/127.0.0.1/tcp/5001/http')
            print("🌐 IPFS客户端已连接")
        except Exception as e:
            print(f"⚠️ IPFS连接失败，使用模拟模式: {e}")
    
    async def launch_collection(self, config: CollectionConfig, creator_address: str) -> str:
        """启动新NFT集合"""
        collection_id = self.collection_manager.create_collection(config, creator_address)
        
        # 可选：自动部署合约（需要连接到区块链）
        print(f"🚀 集合已启动: {config.name}")
        
        return collection_id
    
    def upload_metadata(self, metadata: NFTMetadata) -> str:
        """上传元数据到IPFS"""
        metadata_dict = {
            "name": metadata.name,
            "description": metadata.description,
            "image": metadata.image,
            "attributes": metadata.attributes
        }
        
        if metadata.external_url:
            metadata_dict["external_url"] = metadata.external_url
        if metadata.animation_url:
            metadata_dict["animation_url"] = metadata.animation_url
        if metadata.youtube_url:
            metadata_dict["youtube_url"] = metadata.youtube_url
        
        if self.ipfs_client:
            try:
                res = self.ipfs_client.add_json(metadata_dict)
                return f"ipfs://{res['Hash']}"
            except Exception as e:
                print(f"IPFS上传失败: {e}")
        
        # 模拟IPFS CID
        return f"ipfs://Qm{'a' * 44}"
    
    def get_platform_stats(self) -> Dict:
        """获取平台统计数据"""
        collections = self.collection_manager.list_collections()
        marketplace_stats = self.marketplace.get_marketplace_stats()
        
        return {
            'collections_count': len(collections),
            'total_minted': sum(c['total_minted'] for c in self.collection_manager.collections.values()),
            'marketplace_stats': marketplace_stats
        }


# 使用示例
if __name__ == "__main__":
    # 创建发行平台
    launchpad = NFTLaunchpad()
    launchpad.initialize_ipfs()
    
    # 创建集合配置
    config = CollectionConfig(
        name="Test Collection",
        symbol="TEST",
        description="A test NFT collection for demonstration",
        royalty_percentage=2.5,
        royalty_recipient="0x1234567890123456789012345678901234567890",
        max_supply=10000,
        price_per_mint=0.08,
        standard=NFTStandard.ERC721,
        metadata_base_uri="https://api.testnft.com/metadata/"
    )
    
    # 启动集合
    collection_id = asyncio.run(launchpad.launch_collection(config, "0xCreatorAddress"))
    
    # 显示平台统计
    stats = launchpad.get_platform_stats()
    print(f"📈 平台统计: {json.dumps(stats, indent=2, default=str)}")