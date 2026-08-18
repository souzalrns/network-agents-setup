import { MCPTool } from '../ToolRegistry';
import { Pool } from 'pg';
export function createDatabaseTools(pool: Pool): MCPTool[] {
  return [
    {
      name: 'query_database',
      description: 'Execute a SQL query on the database',
      inputSchema: {
        type: 'object',
        properties: {
          query: { type: 'string', description: 'SQL query to execute' },
          params: { type: 'array', description: 'Parameters for the query', default: [] },
        },
        required: ['query'],
      },
      execute: async ({ query, params = [] }) => {
        try {
          const result = await pool.query(query, params);
          return {
            content: [{ type: 'text', text: JSON.stringify({ rows: result.rows, rowCount: result.rowCount }) }],
            metadata: { rowCount: result.rowCount },
          };
        } catch (error: any) {
          return { content: [{ type: 'text', text: `Database error: ${error.message}` }], isError: true };
        }
      },
    },
    {
      name: 'get_schema',
      description: 'Get database schema information',
      inputSchema: {
        type: 'object',
        properties: {
          table: { type: 'string', description: 'Specific table name (optional)' },
        },
      },
      execute: async ({ table }) => {
        try {
          let query = `SELECT table_name, column_name, data_type, is_nullable FROM information_schema.columns WHERE table_schema = 'public'`;
          if (table) query += ` AND table_name = $1`;
          query += ` ORDER BY table_name, ordinal_position`;
          const result = await pool.query(query, table ? [table] : []);
          const schema: Record<string, any[]> = {};
          for (const row of result.rows) {
            if (!schema[row.table_name]) schema[row.table_name] = [];
            schema[row.table_name].push({ column: row.column_name, type: row.data_type, nullable: row.is_nullable === 'YES' });
          }
          return { content: [{ type: 'text', text: JSON.stringify(schema, null, 2) }] };
        } catch (error: any) {
          return { content: [{ type: 'text', text: `Schema error: ${error.message}` }], isError: true };
        }
      },
    },
  ];
}
