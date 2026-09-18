-- SPDX-License-Identifier: BSD-3-Clause
-- Panel input only. No guest memory writes, dumps, traces or firmware patches.
local panel = assert(os.getenv('MPC2000XL_PANEL_INPUT'), 'Missing panel input path')
dofile(panel)
