import orderApi, { OrderApi as ApiClient } from '../../services/orderApi';
import * as orderTypes from '../../domain/order';
import { parseEnvironment as parseEnv } from '../../config/environment';

export async function loadViaAlias(orderId: string): Promise<orderTypes.Order> {
  return orderApi.getOrder(orderId);
}

export const identifyApi = (): typeof ApiClient => ApiClient;
export const parseFixtureEnvironment = parseEnv;
