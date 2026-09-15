export const formatNumber = (num) => {
  if (num === null || num === undefined) return '0';
  if (typeof num === 'number') {
    return num.toLocaleString();
  }
  return String(num);
};

export const formatFileSize = (bytes) => {
  if (!bytes || bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
};

export const getTypeBadgeColor = (dtype) => {
  const typeStr = String(dtype).toLowerCase();
  if (typeStr.includes('int') || typeStr.includes('float') || typeStr.includes('number')) {
    return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30';
  }
  if (typeStr.includes('date') || typeStr.includes('time')) {
    return 'bg-purple-500/10 text-purple-400 border-purple-500/30';
  }
  if (typeStr.includes('bool')) {
    return 'bg-amber-500/10 text-amber-400 border-amber-500/30';
  }
  return 'bg-blue-500/10 text-blue-400 border-blue-500/30';
};
