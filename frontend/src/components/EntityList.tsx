import React, { useState, useEffect, useCallback } from 'react';
import { Card, List, Tag, Typography, Space, Button, Input, Select, Empty, Spin, message } from 'antd';
import { UserOutlined, SearchOutlined, ReloadOutlined, FilterOutlined } from '@ant-design/icons';
import { apiService } from '../services/api';
import { Entity } from '../types';

const { Text } = Typography;
const { Search } = Input;
const { Option } = Select;

interface EntityListProps {
  onEntitySelect?: (entity: Entity) => void;
}

const EntityList: React.FC<EntityListProps> = ({ onEntitySelect }) => {
  const [entities, setEntities] = useState<Entity[]>([]);
  const [filteredEntities, setFilteredEntities] = useState<Entity[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchText, setSearchText] = useState('');
  const [selectedType, setSelectedType] = useState<string>('all');
  const [entityTypes, setEntityTypes] = useState<string[]>([]);

  const loadEntities = useCallback(async () => {
    setLoading(true);
    try {
      const response = await apiService.getEntities(1000); // Get more entities
      const entityList = response.entities || [];
      setEntities(entityList);
      setFilteredEntities(entityList);
      
      // Extract all entity types
      const types = Array.from(new Set(
        entityList.map(entity => 
          typeof entity === 'string' ? 'UNKNOWN' : (entity.type || 'UNKNOWN')
        )
      ));
      setEntityTypes(types);
      
      if (response.error) {
        message.warning(`Entity loading completed with warnings: ${response.error}`);
      } else {
        message.success(`Successfully loaded ${entityList.length} entities`);
      }
    } catch (error: any) {
      message.error(`Failed to load entities: ${error.response?.data?.detail || error.message}`);
      setEntities([]);
      setFilteredEntities([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadEntities();
  }, [loadEntities]);

  useEffect(() => {
    // Filter entities
    let filtered = entities;
    
    // Filter by type
    if (selectedType !== 'all') {
      filtered = filtered.filter(entity => {
        const entityType = typeof entity === 'string' ? 'UNKNOWN' : (entity.type || 'UNKNOWN');
        return entityType === selectedType;
      });
    }
    
    // Filter by search text
    if (searchText.trim()) {
      filtered = filtered.filter(entity => {
        const entityName = typeof entity === 'string' ? entity : (entity.name || '');
        return entityName.toLowerCase().includes(searchText.toLowerCase());
      });
    }
    
    setFilteredEntities(filtered);
  }, [entities, selectedType, searchText]);

  const getEntityTypeColor = (type: string) => {
    const colors: Record<string, string> = {
      'PERSON': 'blue',
      'ORGANIZATION': 'green',
      'LOCATION': 'orange',
      'EVENT': 'purple',
      'CONCEPT': 'cyan',
      'PRODUCT': 'magenta',
      'UNKNOWN': 'default',
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
            View Details
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
    <Card 
      title="📋 Entity List" 
      style={{ marginBottom: 24 }}
      extra={
        <Button 
          icon={<ReloadOutlined />} 
          onClick={loadEntities}
          loading={loading}
        >
          Refresh
        </Button>
      }
    >
      <Space direction="vertical" style={{ width: '100%' }} size="large">
        <div>
          <Text type="secondary">
            Browse all entities in the knowledge graph with type filtering and search support.
          </Text>
        </div>

        <Space wrap>
          <Search
            placeholder="Search entity names..."
            allowClear
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            style={{ width: 200 }}
            prefix={<SearchOutlined />}
          />
          
          <Select
            value={selectedType}
            onChange={setSelectedType}
            style={{ width: 150 }}
            placeholder="Select Type"
            prefix={<FilterOutlined />}
          >
            <Option value="all">All Types</Option>
            {entityTypes.map(type => (
              <Option key={type} value={type}>
                <Tag color={getEntityTypeColor(type)}>
                  {type}
                </Tag>
              </Option>
            ))}
          </Select>
        </Space>

        {loading ? (
          <div style={{ textAlign: 'center', padding: '50px' }}>
            <Spin size="large" />
            <div style={{ marginTop: 16 }}>
              <Text type="secondary">Loading entity list...</Text>
            </div>
          </div>
        ) : (
          <div>
            <div style={{ marginBottom: 16 }}>
              <Text strong>
                Total {filteredEntities.length} entities
                {selectedType !== 'all' && (
                  <Text type="secondary">(Type: {selectedType})</Text>
                )}
                {searchText && (
                  <Text type="secondary">(Search: "{searchText}")</Text>
                )}
              </Text>
            </div>

            {filteredEntities.length > 0 ? (
              <List
                dataSource={filteredEntities}
                renderItem={renderEntityItem}
                pagination={{
                  pageSize: 20,
                  showSizeChanger: true,
                  showQuickJumper: true,
                  showTotal: (total, range) => 
                    `Page ${range[0]}-${range[1]} of ${total} items`,
                }}
                style={{
                  maxHeight: 500,
                  overflow: 'auto',
                }}
              />
            ) : (
              <Empty
                description={
                  entities.length === 0 
                    ? "No entity data available, please upload documents for processing first"
                    : "No entities found matching criteria"
                }
                image={Empty.PRESENTED_IMAGE_SIMPLE}
              />
            )}
          </div>
        )}
      </Space>
    </Card>
  );
};

export default EntityList;

