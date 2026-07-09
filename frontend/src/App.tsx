import { useState, useEffect } from 'react';
import { Layout, Typography, Tabs, message, Space, Tag, Button, Card } from 'antd';
import { 
  UploadOutlined, 
  SearchOutlined, 
  NodeIndexOutlined, 
  UnorderedListOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined
} from '@ant-design/icons';
import FileUpload from './components/FileUpload';
import EntitySearch from './components/EntitySearch';
import KnowledgeGraph from './components/KnowledgeGraph';
import EntityList from './components/EntityList';
import { apiService, UploadResponse } from './services/api';
import { Entity, GraphNode, GraphLink } from './types';
import './styles/App.css';

const { Header, Content, Sider } = Layout;
const { Title, Text } = Typography;

function App() {
  const [activeTab, setActiveTab] = useState('upload');
  const [healthStatus, setHealthStatus] = useState<'checking' | 'healthy' | 'error'>('checking');
  const [selectedEntity, setSelectedEntity] = useState<Entity | null>(null);

  // Check backend health status
  useEffect(() => {
    const checkHealth = async () => {
      try {
        await apiService.checkHealth();
        setHealthStatus('healthy');
        message.success('Backend service connected successfully');
      } catch (error) {
        setHealthStatus('error');
        message.error('Backend service connection failed, please ensure the backend service is running');
      }
    };

    checkHealth();
  }, []);

  const handleUploadSuccess = (_result: UploadResponse) => {
    message.success('Document processing completed!');
    // Can trigger graph data refresh here
    setActiveTab('graph');
  };

  const handleEntitySelect = (entity: Entity) => {
    setSelectedEntity(entity);
    message.info(`Selected entity: ${entity.name}`);
  };

  const handleNodeClick = (node: GraphNode) => {
    const entity: Entity = {
      id: node.id,
      name: node.name,
      type: node.type || 'UNKNOWN',
      properties: node.properties
    };
    handleEntitySelect(entity);
  };

  const handleLinkClick = (link: GraphLink) => {
    message.info(`Relationship: ${link.source} -> ${link.target} (${link.type})`);
  };

  const getHealthStatusTag = () => {
    switch (healthStatus) {
      case 'healthy':
        return <Tag color="green" icon={<CheckCircleOutlined />}>Service Normal</Tag>;
      case 'error':
        return <Tag color="red" icon={<ExclamationCircleOutlined />}>Service Error</Tag>;
      default:
        return <Tag color="orange">Checking...</Tag>;
    }
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{ background: '#001529', padding: '0 20px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Title level={2} style={{ color: 'white', margin: '15px 0' }}>
          🧠 Knortex - Intelligent Knowledge Graph Platform
        </Title>
        <Space>
          {getHealthStatusTag()}
          <Button 
            type="primary" 
            size="small"
            onClick={() => window.open('http://localhost:8000/docs', '_blank')}
          >
            API Documentation
          </Button>
        </Space>
      </Header>
      
      <Layout>
        <Sider width={300} style={{ background: '#f0f2f5', padding: '20px' }}>
          <div style={{ marginBottom: 20 }}>
            <Title level={4}>📊 System Status</Title>
            <Space direction="vertical" style={{ width: '100%' }}>
              <div>
                <Text strong>Backend Service:</Text>
                {getHealthStatusTag()}
              </div>
              <div>
                <Text strong>Current View:</Text>
                <Tag color="blue">
                  {activeTab === 'upload' && 'Document Upload'}
                  {activeTab === 'search' && 'Entity Search'}
                  {activeTab === 'graph' && 'Graph Visualization'}
                  {activeTab === 'entities' && 'Entity List'}
                </Tag>
              </div>
            </Space>
          </div>

          {selectedEntity && (
            <div>
              <Title level={4}>🎯 Selected Entity</Title>
              <Card size="small" style={{ background: '#e6f7ff', border: '1px solid #91d5ff' }}>
                <Space direction="vertical" style={{ width: '100%' }}>
                  <div>
                    <Text strong>{selectedEntity.name}</Text>
                  </div>
                  <div>
                    <Tag color="blue">{selectedEntity.type}</Tag>
                  </div>
                  {selectedEntity.properties && (
                    <div>
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        Properties: {Object.keys(selectedEntity.properties).length}
                      </Text>
                    </div>
                  )}
                </Space>
              </Card>
            </div>
          )}
        </Sider>

        <Content style={{ padding: '20px', background: '#fff' }}>
          <Tabs 
            activeKey={activeTab} 
            onChange={setActiveTab}
            items={[
              {
                key: 'upload',
                label: (
                  <span>
                    <UploadOutlined />
                    Document Upload
                  </span>
                ),
                children: <FileUpload onUploadSuccess={handleUploadSuccess} />
              },
              {
                key: 'search',
                label: (
                  <span>
                    <SearchOutlined />
                    Entity Search
                  </span>
                ),
                children: <EntitySearch onEntitySelect={handleEntitySelect} />
              },
              {
                key: 'graph',
                label: (
                  <span>
                    <NodeIndexOutlined />
                    Graph Visualization
                  </span>
                ),
                children: (
                  <KnowledgeGraph 
                    onNodeClick={handleNodeClick}
                    onLinkClick={handleLinkClick}
                  />
                )
              },
              {
                key: 'entities',
                label: (
                  <span>
                    <UnorderedListOutlined />
                    Entity List
                  </span>
                ),
                children: <EntityList onEntitySelect={handleEntitySelect} />
              }
            ]}
          />
        </Content>
      </Layout>
    </Layout>
  );
}

export default App;
