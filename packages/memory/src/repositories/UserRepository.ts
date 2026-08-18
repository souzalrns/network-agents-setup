import { PrismaClient } from '@prisma/client';
export class UserRepository {
  constructor(private prisma: PrismaClient) {}
  async create(data: { email: string; name?: string }): Promise<any> {
    return this.prisma.user.create({ data });
  }
  async findById(id: string): Promise<any> {
    return this.prisma.user.findUnique({ where: { id } });
  }
  async findByEmail(email: string): Promise<any> {
    return this.prisma.user.findUnique({ where: { email } });
  }
  async update(id: string, data: any): Promise<any> {
    return this.prisma.user.update({ where: { id }, data });
  }
  async setPreference(userId: string, key: string, value: any): Promise<any> {
    return this.prisma.userPreference.upsert({
      where: { userId_key: { userId, key } },
      update: { value },
      create: { userId, key, value },
    });
  }
  async getPreference(userId: string, key: string): Promise<any> {
    const pref = await this.prisma.userPreference.findUnique({
      where: { userId_key: { userId, key } },
    });
    return pref?.value;
  }
  async delete(id: string): Promise<any> {
    return this.prisma.user.delete({ where: { id } });
  }
}
