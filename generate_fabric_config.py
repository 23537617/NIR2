#!/usr/bin/env python3
"""
Генератор конфигурации Hyperledger Fabric v2.x
Создает минимальную конфигурацию с двумя организациями и одним каналом
"""

import os
import yaml
from pathlib import Path


class FabricConfigGenerator:
    def __init__(self, base_dir="."):
        self.base_dir = Path(base_dir)
        self.config_dir = self.base_dir / "config"
        self.orgs_dir = self.base_dir / "organizations"
        self.channel_dir = self.base_dir / "channel-artifacts"
        
    def create_directories(self):
        """Создает необходимую структуру директорий"""
        directories = [
            self.config_dir,
            self.orgs_dir / "ordererOrganizations" / "example.com",
            self.orgs_dir / "peerOrganizations" / "org1.example.com",
            self.orgs_dir / "peerOrganizations" / "org2.example.com",
            self.channel_dir,
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            print(f"✓ Создана директория: {directory}")
    
    def generate_crypto_config(self):
        """Генерирует crypto-config.yaml"""
        crypto_config = {
            'OrdererOrgs': [
                {
                    'Name': 'Orderer',
                    'Domain': 'example.com',
                    'Specs': [
                        {'Hostname': 'orderer'}
                    ]
                }
            ],
            'PeerOrgs': [
                {
                    'Name': 'Org1',
                    'Domain': 'org1.example.com',
                    'EnableNodeOUs': True,
                    'Template': {
                        'Count': 1
                    },
                    'Users': {
                        'Count': 1
                    }
                },
                {
                    'Name': 'Org2',
                    'Domain': 'org2.example.com',
                    'EnableNodeOUs': True,
                    'Template': {
                        'Count': 1
                    },
                    'Users': {
                        'Count': 1
                    }
                }
            ]
        }
        
        config_path = self.config_dir / "crypto-config.yaml"
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(crypto_config, f, default_flow_style=False, allow_unicode=True)
        print(f"✓ Создан файл: {config_path}")
        return config_path
    
    def generate_configtx(self):
        """Генерирует configtx.yaml"""
        configtx = {
            'Organizations': [
                {
                    'Name': 'OrdererOrg',
                    'ID': 'OrdererMSP',
                    'MSPDir': '../organizations/ordererOrganizations/example.com/msp',
                    'Policies': {
                        'Readers': {
                            'Type': 'Signature',
                            'Rule': "OR('OrdererMSP.member')"
                        },
                        'Writers': {
                            'Type': 'Signature',
                            'Rule': "OR('OrdererMSP.member')"
                        },
                        'Admins': {
                            'Type': 'Signature',
                            'Rule': "OR('OrdererMSP.admin')"
                        }
                    }
                },
                {
                    'Name': 'Org1MSP',
                    'ID': 'Org1MSP',
                    'MSPDir': '../organizations/peerOrganizations/org1.example.com/msp',
                    'Policies': {
                        'Readers': {
                            'Type': 'Signature',
                            'Rule': "OR('Org1MSP.admin', 'Org1MSP.peer', 'Org1MSP.client')"
                        },
                        'Writers': {
                            'Type': 'Signature',
                            'Rule': "OR('Org1MSP.admin', 'Org1MSP.client')"
                        },
                        'Admins': {
                            'Type': 'Signature',
                            'Rule': "OR('Org1MSP.admin')"
                        }
                    },
                    'AnchorPeers': [
                        {
                            'Host': 'peer0.org1.example.com',
                            'Port': 7051
                        }
                    ]
                },
                {
                    'Name': 'Org2MSP',
                    'ID': 'Org2MSP',
                    'MSPDir': '../organizations/peerOrganizations/org2.example.com/msp',
                    'Policies': {
                        'Readers': {
                            'Type': 'Signature',
                            'Rule': "OR('Org2MSP.admin', 'Org2MSP.peer', 'Org2MSP.client')"
                        },
                        'Writers': {
                            'Type': 'Signature',
                            'Rule': "OR('Org2MSP.admin', 'Org2MSP.client')"
                        },
                        'Admins': {
                            'Type': 'Signature',
                            'Rule': "OR('Org2MSP.admin')"
                        }
                    },
                    'AnchorPeers': [
                        {
                            'Host': 'peer0.org2.example.com',
                            'Port': 9051
                        }
                    ]
                }
            ],
            'Capabilities': {
                'Channel': {
                    'V2_0': True
                },
                'Orderer': {
                    'V2_0': True
                },
                'Application': {
                    'V2_0': True
                }
            },
            'Application': {
                'Organizations': None,
                'Policies': {
                    'Readers': {
                        'Type': 'ImplicitMeta',
                        'Rule': 'ANY Readers'
                    },
                    'Writers': {
                        'Type': 'ImplicitMeta',
                        'Rule': 'ANY Writers'
                    },
                    'Admins': {
                        'Type': 'ImplicitMeta',
                        'Rule': 'MAJORITY Admins'
                    },
                    'LifecycleEndorsement': {
                        'Type': 'ImplicitMeta',
                        'Rule': 'MAJORITY Endorsement'
                    },
                    'Endorsement': {
                        'Type': 'ImplicitMeta',
                        'Rule': 'MAJORITY Endorsement'
                    }
                },
                'Capabilities': {
                    'V2_0': True
                }
            },
            'Orderer': {
                'OrdererType': 'etcdraft',
                'EtcdRaft': {
                    'Consenters': [
                        {
                            'Host': 'orderer.example.com',
                            'Port': 7050,
                            'ClientTLSCert': '../organizations/ordererOrganizations/example.com/orderers/orderer.example.com/tls/server.crt',
                            'ServerTLSCert': '../organizations/ordererOrganizations/example.com/orderers/orderer.example.com/tls/server.crt'
                        }
                    ]
                },
                'Organizations': None,
                'Policies': {
                    'Readers': {
                        'Type': 'ImplicitMeta',
                        'Rule': 'ANY Readers'
                    },
                    'Writers': {
                        'Type': 'ImplicitMeta',
                        'Rule': 'ANY Writers'
                    },
                    'Admins': {
                        'Type': 'ImplicitMeta',
                        'Rule': 'MAJORITY Admins'
                    },
                    'BlockValidation': {
                        'Type': 'ImplicitMeta',
                        'Rule': 'ANY Writers'
                    }
                },
                'Capabilities': {
                    'V2_0': True
                },
                'BatchTimeout': '2s',
                'BatchSize': {
                    'MaxMessageCount': 10,
                    'AbsoluteMaxBytes': '99 MB',
                    'PreferredMaxBytes': '512 KB'
                }
            },
            'Channel': {
                'Policies': {
                    'Readers': {
                        'Type': 'ImplicitMeta',
                        'Rule': 'ANY Readers'
                    },
                    'Writers': {
                        'Type': 'ImplicitMeta',
                        'Rule': 'ANY Writers'
                    },
                    'Admins': {
                        'Type': 'ImplicitMeta',
                        'Rule': 'MAJORITY Admins'
                    }
                },
                'Capabilities': {
                    'V2_0': True
                }
            },
            'Profiles': {
                'TwoOrgsOrdererGenesis': {
                    'Orderer': {
                        '<<': '*Orderer',
                        'Organizations': [
                            {
                                '<<': '*OrdererOrg'
                            }
                        ]
                    },
                    'Consortiums': {
                        'SampleConsortium': {
                            'Organizations': [
                                {
                                    '<<': '*Org1MSP'
                                },
                                {
                                    '<<': '*Org2MSP'
                                }
                            ]
                        }
                    }
                },
                'TwoOrgsChannel': {
                    'Consortium': 'SampleConsortium',
                    'Application': {
                        '<<': '*Application',
                        'Organizations': [
                            {
                                '<<': '*Org1MSP'
                            },
                            {
                                '<<': '*Org2MSP'
                            }
                        ]
                    }
                }
            }
        }
        
        config_path = self.config_dir / "configtx.yaml"
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(configtx, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        print(f"✓ Создан файл: {config_path}")
        return config_path
    
    def generate_docker_compose(self):
        """Генерирует docker-compose.yaml с CA серверами"""
        docker_compose = {
            'version': '3.8',
            'services': {
                'ca_orderer': {
                    'container_name': 'ca_orderer',
                    'image': 'hyperledger/fabric-ca:1.5',
                    'environment': [
                        'FABRIC_CA_HOME=/etc/hyperledger/fabric-ca-server',
                        'FABRIC_CA_SERVER_CA_NAME=ca-orderer',
                        'FABRIC_CA_SERVER_TLS_ENABLED=true',
                        'FABRIC_CA_SERVER_PORT=7054',
                        'FABRIC_CA_SERVER_OPERATIONS_LISTENADDRESS=0.0.0.0:9443'
                    ],
                    'ports': [
                        '7054:7054',
                        '9443:9443'
                    ],
                    'command': 'sh -c "fabric-ca-server start -b admin:adminpw -d"',
                    'volumes': [
                        './organizations/fabric-ca/ordererOrg:/etc/hyperledger/fabric-ca-server-config'
                    ],
                    'networks': [
                        'fabric-network'
                    ]
                },
                'ca_org1': {
                    'container_name': 'ca_org1',
                    'image': 'hyperledger/fabric-ca:1.5',
                    'environment': [
                        'FABRIC_CA_HOME=/etc/hyperledger/fabric-ca-server',
                        'FABRIC_CA_SERVER_CA_NAME=ca-org1',
                        'FABRIC_CA_SERVER_TLS_ENABLED=true',
                        'FABRIC_CA_SERVER_PORT=7054',
                        'FABRIC_CA_SERVER_OPERATIONS_LISTENADDRESS=0.0.0.0:9444'
                    ],
                    'ports': [
                        '7054:7054',
                        '9444:9444'
                    ],
                    'command': 'sh -c "fabric-ca-server start -b admin:adminpw -d"',
                    'volumes': [
                        './organizations/fabric-ca/org1:/etc/hyperledger/fabric-ca-server-config'
                    ],
                    'networks': [
                        'fabric-network'
                    ]
                },
                'ca_org2': {
                    'container_name': 'ca_org2',
                    'image': 'hyperledger/fabric-ca:1.5',
                    'environment': [
                        'FABRIC_CA_HOME=/etc/hyperledger/fabric-ca-server',
                        'FABRIC_CA_SERVER_CA_NAME=ca-org2',
                        'FABRIC_CA_SERVER_TLS_ENABLED=true',
                        'FABRIC_CA_SERVER_PORT=7054',
                        'FABRIC_CA_SERVER_OPERATIONS_LISTENADDRESS=0.0.0.0:9445'
                    ],
                    'ports': [
                        '8054:7054',
                        '9445:9445'
                    ],
                    'command': 'sh -c "fabric-ca-server start -b admin:adminpw -d"',
                    'volumes': [
                        './organizations/fabric-ca/org2:/etc/hyperledger/fabric-ca-server-config'
                    ],
                    'networks': [
                        'fabric-network'
                    ]
                },
                'orderer0': {
                    'container_name': 'orderer0',
                    'image': 'hyperledger/fabric-orderer:2.5',
                    'environment': [
                        'FABRIC_LOGGING_SPEC=INFO',
                        'ORDERER_GENERAL_LISTENADDRESS=0.0.0.0',
                        'ORDERER_GENERAL_LISTENPORT=7050',
                        'ORDERER_GENERAL_BOOTSTRAPMETHOD=file',
                        'ORDERER_GENERAL_BOOTSTRAPFILE=/var/hyperledger/orderer/orderer.genesis.block',
                        'ORDERER_GENERAL_LOCALMSPID=OrdererMSP',
                        'ORDERER_GENERAL_LOCALMSPDIR=/var/hyperledger/orderer/msp',
                        'ORDERER_GENERAL_TLS_ENABLED=true',
                        'ORDERER_GENERAL_TLS_PRIVATEKEY=/var/hyperledger/orderer/tls/server.key',
                        'ORDERER_GENERAL_TLS_CERTIFICATE=/var/hyperledger/orderer/tls/server.crt',
                        'ORDERER_GENERAL_TLS_ROOTCAS=[/var/hyperledger/orderer/tls/ca.crt]',
                        'ORDERER_GENERAL_CLUSTER_CLIENTCERTIFICATE=/var/hyperledger/orderer/tls/server.crt',
                        'ORDERER_GENERAL_CLUSTER_CLIENTPRIVATEKEY=/var/hyperledger/orderer/tls/server.key',
                        'ORDERER_GENERAL_CLUSTER_ROOTCAS=[/var/hyperledger/orderer/tls/ca.crt]',
                        'ORDERER_KAFKA_TOPIC_REPLICATIONFACTOR=1',
                        'ORDERER_KAFKA_VERBOSE=true',
                        'ORDERER_GENERAL_GENESISMETHOD=file',
                        'ORDERER_GENERAL_GENESISFILE=/var/hyperledger/orderer/orderer.genesis.block',
                        'ORDERER_FILELEDGER_LOCATION=/var/hyperledger/production/orderer',
                        'ORDERER_GENERAL_GENESISPROFILE=TwoOrgsOrdererGenesis'
                    ],
                    'working_dir': '/opt/gopath/src/github.com/hyperledger/fabric',
                    'command': 'orderer',
                    'volumes': [
                        './channel-artifacts/genesis.block:/var/hyperledger/orderer/orderer.genesis.block',
                        './organizations/ordererOrganizations/example.com/orderers/orderer.example.com/msp:/var/hyperledger/orderer/msp',
                        './organizations/ordererOrganizations/example.com/orderers/orderer.example.com/tls/:/var/hyperledger/orderer/tls',
                        'orderer0:/var/hyperledger/production/orderer'
                    ],
                    'ports': [
                        '7050:7050'
                    ],
                    'depends_on': [
                        'ca_orderer'
                    ],
                    'networks': [
                        'fabric-network'
                    ]
                },
                'peer0.org1.example.com': {
                    'container_name': 'peer0.org1.example.com',
                    'image': 'hyperledger/fabric-peer:2.5',
                    'environment': [
                        'CORE_VM_ENDPOINT=unix:///host/var/run/docker.sock',
                        'CORE_VM_DOCKER_HOSTCONFIG_NETWORKMODE=fabric-network',
                        'FABRIC_LOGGING_SPEC=INFO',
                        'CORE_PEER_TLS_ENABLED=true',
                        'CORE_PEER_PROFILE_ENABLED=true',
                        'CORE_PEER_TLS_CERT_FILE=/etc/hyperledger/fabric/tls/server.crt',
                        'CORE_PEER_TLS_KEY_FILE=/etc/hyperledger/fabric/tls/server.key',
                        'CORE_PEER_TLS_ROOTCERT_FILE=/etc/hyperledger/fabric/tls/ca.crt',
                        'CORE_PEER_ID=peer0.org1.example.com',
                        'CORE_PEER_ADDRESS=peer0.org1.example.com:7051',
                        'CORE_PEER_LISTENADDRESS=0.0.0.0:7051',
                        'CORE_PEER_CHAINCODEADDRESS=peer0.org1.example.com:7052',
                        'CORE_PEER_CHAINCODELISTENADDRESS=0.0.0.0:7052',
                        'CORE_PEER_GOSSIP_BOOTSTRAP=peer0.org1.example.com:7051',
                        'CORE_PEER_GOSSIP_EXTERNALENDPOINT=peer0.org1.example.com:7051',
                        'CORE_PEER_LOCALMSPID=Org1MSP',
                        'CORE_OPERATIONS_LISTENADDRESS=0.0.0.0:9443',
                        'CHAINCODE_AS_A_SERVICE_BUILDER_CONFIG={"peers":[{"name":"peer0.org1.example.com","address":"peer0.org1.example.com:7052","tls_required":true,"client_tls_cert":"/etc/hyperledger/fabric/peer/tls/ca.crt","root_cert":"/etc/hyperledger/fabric/peer/tls/ca.crt"}]}',
                        'CORE_PEER_TLS_CLIENTAUTHREQUIRED=true',
                        'CORE_PEER_TLS_CLIENTROOTCAS_FILES=/etc/hyperledger/fabric/tls/ca.crt',
                        'CORE_PEER_TLS_CLIENTCERT_FILE=/etc/hyperledger/fabric/tls/server.crt',
                        'CORE_PEER_TLS_CLIENTKEY_FILE=/etc/hyperledger/fabric/tls/server.key',
                        'CORE_PEER_GOSSIP_USELEADERELECTION=true',
                        'CORE_PEER_GOSSIP_ORGLEADER=false',
                        'CORE_PEER_GOSSIP_SKIPHANDSHAKE=true',
                        'CORE_PEER_MSPCONFIGPATH=/etc/hyperledger/fabric/msp',
                        'CORE_LEDGER_STATE_STATEDATABASE=CouchDB',
                        'CORE_LEDGER_STATE_COUCHDBCONFIG_COUCHDBADDRESS=couchdb0:5984',
                        'CORE_LEDGER_STATE_COUCHDBCONFIG_USERNAME=admin',
                        'CORE_LEDGER_STATE_COUCHDBCONFIG_PASSWORD=adminpw'
                    ],
                    'volumes': [
                        '/var/run/:/host/var/run/',
                        './organizations/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/msp:/etc/hyperledger/fabric/msp',
                        './organizations/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/:/etc/hyperledger/fabric/tls',
                        'peer0.org1.example.com:/var/hyperledger/production'
                    ],
                    'working_dir': '/opt/gopath/src/github.com/hyperledger/fabric/peer',
                    'command': 'peer node start',
                    'ports': [
                        '7051:7051',
                        '9443:9443'
                    ],
                    'depends_on': [
                        'orderer0',
                        'ca_org1',
                        'couchdb0'
                    ],
                    'networks': [
                        'fabric-network'
                    ]
                },
                'couchdb0': {
                    'container_name': 'couchdb0',
                    'image': 'couchdb:3.2',
                    'environment': [
                        'COUCHDB_USER=admin',
                        'COUCHDB_PASSWORD=adminpw'
                    ],
                    'ports': [
                        '5984:5984'
                    ],
                    'networks': [
                        'fabric-network'
                    ]
                },
                'peer0.org2.example.com': {
                    'container_name': 'peer0.org2.example.com',
                    'image': 'hyperledger/fabric-peer:2.5',
                    'environment': [
                        'CORE_VM_ENDPOINT=unix:///host/var/run/docker.sock',
                        'CORE_VM_DOCKER_HOSTCONFIG_NETWORKMODE=fabric-network',
                        'FABRIC_LOGGING_SPEC=INFO',
                        'CORE_PEER_TLS_ENABLED=true',
                        'CORE_PEER_PROFILE_ENABLED=true',
                        'CORE_PEER_TLS_CERT_FILE=/etc/hyperledger/fabric/tls/server.crt',
                        'CORE_PEER_TLS_KEY_FILE=/etc/hyperledger/fabric/tls/server.key',
                        'CORE_PEER_TLS_ROOTCERT_FILE=/etc/hyperledger/fabric/tls/ca.crt',
                        'CORE_PEER_ID=peer0.org2.example.com',
                        'CORE_PEER_ADDRESS=peer0.org2.example.com:9051',
                        'CORE_PEER_LISTENADDRESS=0.0.0.0:9051',
                        'CORE_PEER_CHAINCODEADDRESS=peer0.org2.example.com:9052',
                        'CORE_PEER_CHAINCODELISTENADDRESS=0.0.0.0:9052',
                        'CORE_PEER_GOSSIP_BOOTSTRAP=peer0.org2.example.com:9051',
                        'CORE_PEER_GOSSIP_EXTERNALENDPOINT=peer0.org2.example.com:9051',
                        'CORE_PEER_LOCALMSPID=Org2MSP',
                        'CORE_OPERATIONS_LISTENADDRESS=0.0.0.0:9444',
                        'CHAINCODE_AS_A_SERVICE_BUILDER_CONFIG={"peers":[{"name":"peer0.org2.example.com","address":"peer0.org2.example.com:9052","tls_required":true,"client_tls_cert":"/etc/hyperledger/fabric/peer/tls/ca.crt","root_cert":"/etc/hyperledger/fabric/peer/tls/ca.crt"}]}',
                        'CORE_PEER_TLS_CLIENTAUTHREQUIRED=true',
                        'CORE_PEER_TLS_CLIENTROOTCAS_FILES=/etc/hyperledger/fabric/tls/ca.crt',
                        'CORE_PEER_TLS_CLIENTCERT_FILE=/etc/hyperledger/fabric/tls/server.crt',
                        'CORE_PEER_TLS_CLIENTKEY_FILE=/etc/hyperledger/fabric/tls/server.key',
                        'CORE_PEER_GOSSIP_USELEADERELECTION=true',
                        'CORE_PEER_GOSSIP_ORGLEADER=false',
                        'CORE_PEER_GOSSIP_SKIPHANDSHAKE=true',
                        'CORE_PEER_MSPCONFIGPATH=/etc/hyperledger/fabric/msp',
                        'CORE_LEDGER_STATE_STATEDATABASE=CouchDB',
                        'CORE_LEDGER_STATE_COUCHDBCONFIG_COUCHDBADDRESS=couchdb1:5984',
                        'CORE_LEDGER_STATE_COUCHDBCONFIG_USERNAME=admin',
                        'CORE_LEDGER_STATE_COUCHDBCONFIG_PASSWORD=adminpw'
                    ],
                    'volumes': [
                        '/var/run/:/host/var/run/',
                        './organizations/peerOrganizations/org2.example.com/peers/peer0.org2.example.com/msp:/etc/hyperledger/fabric/msp',
                        './organizations/peerOrganizations/org2.example.com/peers/peer0.org2.example.com/tls/:/etc/hyperledger/fabric/tls',
                        'peer0.org2.example.com:/var/hyperledger/production'
                    ],
                    'working_dir': '/opt/gopath/src/github.com/hyperledger/fabric/peer',
                    'command': 'peer node start',
                    'ports': [
                        '9051:9051',
                        '9444:9444'
                    ],
                    'depends_on': [
                        'orderer0',
                        'ca_org2',
                        'couchdb1'
                    ],
                    'networks': [
                        'fabric-network'
                    ]
                },
                'couchdb1': {
                    'container_name': 'couchdb1',
                    'image': 'couchdb:3.2',
                    'environment': [
                        'COUCHDB_USER=admin',
                        'COUCHDB_PASSWORD=adminpw'
                    ],
                    'ports': [
                        '5985:5984'
                    ],
                    'networks': [
                        'fabric-network'
                    ]
                }
            },
            'networks': {
                'fabric-network': {
                    'driver': 'bridge'
                }
            },
            'volumes': {
                'orderer0': None,
                'peer0.org1.example.com': None,
                'peer0.org2.example.com': None
            }
        }
        
        compose_path = self.base_dir / "docker-compose.yaml"
        with open(compose_path, 'w', encoding='utf-8') as f:
            yaml.dump(docker_compose, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        print(f"✓ Создан файл: {compose_path}")
        return compose_path
    
    def generate_all(self):
        """Генерирует всю конфигурацию"""
        print("=" * 60)
        print("Генерация конфигурации Hyperledger Fabric v2.x")
        print("=" * 60)
        
        self.create_directories()
        self.generate_crypto_config()
        self.generate_configtx()
        self.generate_docker_compose()
        
        print("\n" + "=" * 60)
        print("✓ Конфигурация успешно создана!")
        print("=" * 60)
        print("\nСледующие шаги:")
        print("1. Установите инструменты Hyperledger Fabric (cryptogen, configtxgen)")
        print("2. Запустите network_setup.py для инструкций по генерации артефактов")
        print("3. Используйте docker-compose up -d для запуска сети")


def main():
    generator = FabricConfigGenerator()
    generator.generate_all()


if __name__ == "__main__":
    main()

