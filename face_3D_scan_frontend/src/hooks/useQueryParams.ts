import { useSearchParams } from 'react-router-dom';

export const useQueryParams = () => {
  const [searchParams] = useSearchParams();
  
  const getEmployeeId = (): string | null => {
    return searchParams.get('id');
  };

  const getAction = (): string | null => {
    return searchParams.get('action');
  };

  return {
    getEmployeeId,
    getAction,
    searchParams,
  };
};
