import React, { useState, useCallback } from 'react';
import { Upload, Button, message, Card, Progress, Typography, Space, Tag } from 'antd';
import { InboxOutlined, FileTextOutlined, FilePdfOutlined, FileWordOutlined } from '@ant-design/icons';
import { apiService, UploadResponse } from '../services/api';
import { FileUpload as FileUploadType } from '../types';

const { Dragger } = Upload;
const { Title, Text } = Typography;

interface FileUploadProps {
  onUploadSuccess?: (result: UploadResponse) => void;
}

const FileUpload: React.FC<FileUploadProps> = ({ onUploadSuccess }) => {
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadResult, setUploadResult] = useState<UploadResponse | null>(null);

  const handleUpload = useCallback(async (file: File) => {
    setUploading(true);
    setUploadProgress(0);
    setUploadResult(null);

    try {
      // Simulate upload progress
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return 90;
          }
          return prev + 10;
        });
      }, 200);

      const result = await apiService.uploadFile(file);
      
      clearInterval(progressInterval);
      setUploadProgress(100);
      setUploadResult(result);
      setUploading(false);
      
      message.success('File uploaded and processed successfully!');
      onUploadSuccess?.(result);
      
    } catch (error: any) {
      setUploading(false);
      setUploadProgress(0);
      message.error(`Upload failed: ${error.response?.data?.detail || error.message}`);
    }
  }, [onUploadSuccess]);

  const getFileIcon = (filename: string) => {
    const ext = filename.split('.').pop()?.toLowerCase();
    switch (ext) {
      case 'pdf':
        return <FilePdfOutlined style={{ color: '#ff4d4f' }} />;
      case 'docx':
        return <FileWordOutlined style={{ color: '#1890ff' }} />;
      case 'txt':
        return <FileTextOutlined style={{ color: '#52c41a' }} />;
      default:
        return <FileTextOutlined />;
    }
  };

  const uploadProps = {
    name: 'file',
    multiple: false,
    accept: '.pdf,.docx,.txt',
    beforeUpload: (file: File) => {
      const isValidType = file.type === 'application/pdf' || 
                         file.type === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' ||
                         file.type === 'text/plain';
      
      if (!isValidType) {
        message.error('Only PDF, Word documents and text files are supported!');
        return false;
      }

      const isLt10M = file.size / 1024 / 1024 < 10;
      if (!isLt10M) {
        message.error('File size cannot exceed 10MB!');
        return false;
      }

      handleUpload(file);
      return false; // Prevent automatic upload
    },
  };

  return (
    <Card title="📄 Document Upload & Processing" style={{ marginBottom: 24 }}>
      <Space direction="vertical" style={{ width: '100%' }} size="large">
        <div>
          <Text type="secondary">
            Support uploading PDF, Word documents and text files. The system will automatically extract entity and relationship information.
          </Text>
        </div>

        <Dragger {...uploadProps} disabled={uploading}>
          <p className="ant-upload-drag-icon">
            <InboxOutlined />
          </p>
          <p className="ant-upload-text">
            {uploading ? 'Processing file...' : 'Click or drag files to this area to upload'}
          </p>
          <p className="ant-upload-hint">
            Support single file upload, only PDF, DOCX, TXT formats
          </p>
        </Dragger>

        {uploading && (
          <div>
            <Text>Processing Progress:</Text>
            <Progress percent={uploadProgress} status="active" />
          </div>
        )}

        {uploadResult && (
          <Card size="small" style={{ background: '#f6ffed', border: '1px solid #b7eb8f' }}>
            <Title level={5}>✅ Processing Complete</Title>
            <Space direction="vertical" style={{ width: '100%' }}>
              <div>
                <Text strong>File Name:</Text>
                <Space>
                  {getFileIcon(uploadResult.filename)}
                  <Text>{uploadResult.filename}</Text>
                </Space>
              </div>
              
              <div>
                <Text strong>File Type:</Text>
                <Tag color="blue">{uploadResult.file_type}</Tag>
              </div>
              
              <div>
                <Text strong>Content Length:</Text>
                <Text>{uploadResult.content_length.toLocaleString()} characters</Text>
              </div>
              
              <div>
                <Text strong>Processing Status:</Text>
                <Tag color="green">{uploadResult.status}</Tag>
              </div>

              {uploadResult.extraction_result && (
                <div>
                  <Text strong>Extraction Result:</Text>
                  <div style={{ marginTop: 8, padding: 12, background: '#fafafa', borderRadius: 4 }}>
                    <pre style={{ margin: 0, fontSize: 12, maxHeight: 200, overflow: 'auto' }}>
                      {JSON.stringify(uploadResult.extraction_result, null, 2)}
                    </pre>
                  </div>
                </div>
              )}

              {uploadResult.storage_result?.error && (
                <div>
                  <Text strong style={{ color: '#ff4d4f' }}>Storage Warning:</Text>
                  <Text type="danger">{uploadResult.storage_result.error}</Text>
                </div>
              )}
            </Space>
          </Card>
        )}
      </Space>
    </Card>
  );
};

export default FileUpload;
