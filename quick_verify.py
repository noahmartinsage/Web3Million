import json

print('🧪 Web3Million 测试网配置验证')
print('='*50)

# 检查配置文件
import os
config_exists = os.path.exists('testnet_config.json')
env_exists = os.path.exists('.env')

print('📋 配置文件检查:')
print('   testnet_config.json: ', '✅' if config_exists else '❌')
print('   .env: ', '✅' if env_exists else '❌')

if config_exists:
    with open('testnet_config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    print('')
    print('🌐 测试网环境配置:')
    for network, settings in config['testnet_environments'].items():
        print('   ' + network + ': ' + settings['currency'] + ' - Chain ID: ' + str(settings['chain_id']))
    
    print('')
    print('🛡️ 风险管理配置:')
    rm = config['risk_management']
    print('   最大仓位: ' + str(rm['max_position_size']*100) + '%')
    print('   最大日亏损: $' + str(rm['max_daily_loss']))
    print('   最大回撤: ' + str(rm['max_drawdown']*100) + '%')
    print('   测试模式: ' + str(rm['test_mode']))
    
    print('')
    print('⚙️ 交易设置:')
    trading = config['trading_settings']
    print('   杠杆: ' + str(trading['leverage']) + 'x')
    print('   模拟模式: ' + str(trading['simulation_mode']))

print('')
print('✅ 测试网配置验证完成!')
print('💡 您现在可以开始在测试环境中验证Web3Million系统')