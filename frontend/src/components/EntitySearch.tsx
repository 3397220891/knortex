import React, { useState, useCallback } from 'react';
import { Input, Button, Card, List, Tag, Typography, Space, Empty, Spin, message } from 'antd';
import { SearchOutlined, UserOutlined, LinkOutlined } from '@ant-design/icons';
import { apiService } from '../services/api';
import { Entity } from '../types';

const { Search } = Input;
const { Title, Text } = Typography;

interface EntitySearchProps {
  onEntitySelect?: (entity: Entity) => void;
}

const EntitySearch: React.FC<EntitySearchProps> = ({ onEntitySelect }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<Entity[]>([]);
  const [loading, setLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);

  const handleSearch = useCallback(async (query: string) => {
    if (!query.trim()) {
      message.warning('Please enter search keywords');
      return;
    }

    setLoading(true);
    setHasSearched(true);

    try {
      const response = await apiService.searchEntities(query);
      setSearchResults(response.results || []);
      
      if (response.error) {
        message.warning(`Search completed with warnings: ${response.error}`);
      } else if (response.results?.length === 0) {
        message.info('No related entities found');
      } else {
        message.success(`Found ${response.results.length} related entities`);
      }
    } catch (error: any) {
      message.error(`Search failed: ${error.response?.data?.detail || error.message}`);
      setSearchResults([]);
    } finally {
      setLoading(false);
    }
  }, []);

  const getEntityTypeColor = (type: string) => {
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

  const renderEntityItem = (entity: any, index: number) => {
    const entityData = typeof entity === 'string' ? { name: entity, type: 'UNKNOWN' } : entity;
    
    return (
      <List.Item
        key={index}
        style={{ cursor: 'pointer' }}
        onClick={() => onEntitySelect?.(entityData)}
        actions={[
          <Button 
            type="link" 
            size="small"
            onClick={(e) => {
              e.stopPropagation();
              onEntitySelect?.(entityData);
            }}
          >
            查看详情
          </Button>
        ]}
      >
        <List.Item.Meta
          avatar={<UserOutlined style={{ fontSize: 20, color: '#1890ff' }} />}
          title={
            <Space>
              <Text strong>{entityData.name || entityData}</Text>
              <Tag color={getEntityTypeColor(entityData.type)}>
                {entityData.type || 'UNKNOWN'}
              </Tag>
            </Space>
          }
          description={
            <Space direction="vertical" size="small">
              {entityData.properties && (
                <div>
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    Properties: {Object.keys(entityData.properties).length}
                  </Text>
                </div>
              )}
              {entityData.labels && entityData.labels.length > 0 && (
                <div>
                  <Space size="small">
                    {entityData.labels.map((label: string, idx: number) => (
                      <Tag key={idx}>{label}</Tag>
                    ))}
                  </Space>
                </div>
              )}
            </Space>
          }
        />
      </List.Item>
    );
  };

  return (
    <Card title="🔍 Entity Search" style={{ marginBottom: 24 }}>
      <Space direction="vertical" style={{ width: '100%' }} size="large">
        <div>
          <Text type="secondary">
            Search entities in the knowledge graph with fuzzy matching and type filtering support.
          </Text>
        </div>

        <Search
          placeholder="Enter entity name to search..."
          allowClear
          enterButton={
            <Button type="primary" icon={<SearchOutlined />} loading={loading}>
              Search
            </Button>
          }
          size="large"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          onSearch={handleSearch}
          loading={loading}
        />

        {loading && (
          <div style={{ textAlign: 'center', padding: '20px' }}>
            <Spin size="large" />
            <div style={{ marginTop: 16 }}>
              <Text type="secondary">Searching entities...</Text>
            </div>
          </div>
        )}

        {!loading && hasSearched && (
          <div>
            <Title level={5}>
              <LinkOutlined /> Search Results
              {searchResults.length > 0 && (
                <Text type="secondary" style={{ fontSize: 14, fontWeight: 'normal' }}>
                  (Total {searchResults.length} results)
                </Text>
              )}
            </Title>

            {searchResults.length > 0 ? (
              <List
                dataSource={searchResults}
                renderItem={renderEntityItem}
                pagination={{
                  pageSize: 10,
                  showSizeChanger: true,
                  showQuickJumper: true,
                  showTotal: (total, range) => 
                    `Page ${range[0]}-${range[1]} of ${total} items`,
                }}
                style={{
                  maxHeight: 400,
                  overflow: 'auto',
                }}
              />
            ) : (
              <Empty
                description="No related entities found"
                image={Empty.PRESENTED_IMAGE_SIMPLE}
              />
            )}
          </div>
        )}
      </Space>
    </Card>
  );
};

export default EntitySearch;
