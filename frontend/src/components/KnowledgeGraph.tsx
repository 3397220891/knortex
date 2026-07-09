import React, { useEffect, useState, useCallback } from 'react';
import { Card, Button, Slider, Typography, Space, Spin, message, List, Tag } from 'antd';
import { ReloadOutlined, NodeIndexOutlined, LinkOutlined } from '@ant-design/icons';
import { apiService } from '../services/api';
import { GraphData, GraphNode, GraphLink } from '../types';

const { Title, Text } = Typography;

interface KnowledgeGraphProps {
  onNodeClick?: (node: GraphNode) => void;
  onLinkClick?: (link: GraphLink) => void;
}

const KnowledgeGraph: React.FC<KnowledgeGraphProps> = ({ onNodeClick, onLinkClick }) => {
  const [graphData, setGraphData] = useState<GraphData>({ nodes: [], links: [] });
  const [loading, setLoading] = useState(false);
  const [nodeLimit, setNodeLimit] = useState(100);

  const loadGraphData = useCallback(async (limit: number = 100) => {
    setLoading(true);
    try {
      const response = await apiService.getGraphData(limit);
      setGraphData(response);
      
      if (response.error) {
        message.warning(`Graph loading completed with warnings: ${response.error}`);
      } else {
        message.success(`Successfully loaded ${response.nodes.length} nodes, ${response.links.length} relationships`);
      }
    } catch (error: any) {
      message.error(`Failed to load graph: ${error.response?.data?.detail || error.message}`);
      setGraphData({ nodes: [], links: [] });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadGraphData(nodeLimit);
  }, [loadGraphData, nodeLimit]);

  const getNodeTypeColor = (type: string) => {
    const colors: Record<string, string> = {
      'PERSON': 'blue',
      'ORGANIZATION': 'green',
      'LOCATION': 'orange',
      'EVENT': 'purple',
      'CONCEPT': 'cyan',
      'PRODUCT': 'magenta',
      'default': 'default'
    };
    return colors[type] || colors.default;
  };

  const handleNodeClick = (node: GraphNode) => {
    onNodeClick?.(node);
  };

  const handleLinkClick = (link: GraphLink) => {
    onLinkClick?.(link);
  };

  const handleRefresh = () => {
    loadGraphData(nodeLimit);
  };

  return (
    <Card 
      title="🕸️ Knowledge Graph Visualization" 
      style={{ marginBottom: 24 }}
      extra={
        <Button 
          icon={<ReloadOutlined />} 
          onClick={handleRefresh}
          loading={loading}
        >
          Refresh
        </Button>
      }
    >
      <Space direction="vertical" style={{ width: '100%' }} size="large">
        <div>
          <Text type="secondary">
            Visualize entities and relationships in the knowledge graph with interactive exploration support.
          </Text>
        </div>

        <div>
          <Text strong>Node Limit:</Text>
          <Slider
            min={10}
            max={500}
            step={10}
            value={nodeLimit}
            onChange={setNodeLimit}
            style={{ width: 200, marginLeft: 16 }}
            marks={{
              10: '10',
              100: '100',
              200: '200',
              500: '500'
            }}
          />
        </div>

        {loading ? (
          <div style={{ textAlign: 'center', padding: '50px' }}>
            <Spin size="large" />
            <div style={{ marginTop: 16 }}>
              <Text type="secondary">Loading graph data...</Text>
            </div>
          </div>
        ) : (
          <div>
            {graphData.nodes.length > 0 ? (
              <Space direction="vertical" style={{ width: '100%' }} size="large">
                <div>
                  <Title level={5}>
                    <NodeIndexOutlined /> Node List ({graphData.nodes.length})
                  </Title>
                  <List
                    dataSource={graphData.nodes}
                    renderItem={(node) => (
                      <List.Item
                        style={{ cursor: 'pointer' }}
                        onClick={() => handleNodeClick(node)}
                        actions={[
                          <Button 
                            type="link" 
                            size="small"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleNodeClick(node);
                            }}
                          >
                            View Details
                          </Button>
                        ]}
                      >
                        <List.Item.Meta
                          avatar={<NodeIndexOutlined style={{ fontSize: 20, color: '#1890ff' }} />}
                          title={
                            <Space>
                              <Text strong>{node.name}</Text>
                              <Tag color={getNodeTypeColor(node.type)}>
                                {node.type || 'UNKNOWN'}
                              </Tag>
                            </Space>
                          }
                          description={
                            node.properties && (
                              <Text type="secondary" style={{ fontSize: 12 }}>
                                Properties: {Object.keys(node.properties).length}
                              </Text>
                            )
                          }
                        />
                      </List.Item>
                    )}
                    pagination={{
                      pageSize: 10,
                      showSizeChanger: true,
                      showQuickJumper: true,
                      showTotal: (total, range) => 
                        `Page ${range[0]}-${range[1]} of ${total} items`,
                    }}
                    style={{
                      maxHeight: 300,
                      overflow: 'auto',
                    }}
                  />
                </div>

                {graphData.links.length > 0 && (
                  <div>
                    <Title level={5}>
                      <LinkOutlined /> Relationship List ({graphData.links.length})
                    </Title>
                    <List
                      dataSource={graphData.links}
                      renderItem={(link) => (
                        <List.Item
                          style={{ cursor: 'pointer' }}
                          onClick={() => handleLinkClick(link)}
                          actions={[
                            <Button 
                              type="link" 
                              size="small"
                              onClick={(e) => {
                                e.stopPropagation();
                                handleLinkClick(link);
                              }}
                            >
                              View Details
                            </Button>
                          ]}
                        >
                          <List.Item.Meta
                            avatar={<LinkOutlined style={{ fontSize: 20, color: '#52c41a' }} />}
                            title={
                              <Space>
                                <Text strong>{link.source}</Text>
                                <Text type="secondary">→</Text>
                                <Text strong>{link.target}</Text>
                                <Tag color="green">{link.type || 'RELATION'}</Tag>
                              </Space>
                            }
                            description={
                              link.properties && (
                                <Text type="secondary" style={{ fontSize: 12 }}>
                                  Properties: {Object.keys(link.properties).length}
                                </Text>
                              )
                            }
                          />
                        </List.Item>
                      )}
                      pagination={{
                        pageSize: 10,
                        showSizeChanger: true,
                        showQuickJumper: true,
                        showTotal: (total, range) => 
                          `Page ${range[0]}-${range[1]} of ${total} items`,
                      }}
                      style={{
                        maxHeight: 300,
                        overflow: 'auto',
                      }}
                    />
                  </div>
                )}
              </Space>
            ) : (
              <div style={{ textAlign: 'center', padding: '50px' }}>
                <Text type="secondary">No graph data available, please upload documents for processing first</Text>
              </div>
            )}
          </div>
        )}
      </Space>
    </Card>
  );
};

export default KnowledgeGraph;
