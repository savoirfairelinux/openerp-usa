# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011 NovaPoint Group LLC (<http://www.novapointgroup.com>)
#    Copyright (C) 2004-2010 OpenERP SA (<http://www.openerp.com>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
##############################################################################

from Crypto.PublicKey import RSA
import base64
import tools

def rsa_enc():
    """
    Generate a key for RSA Encryption
    @return : key
    """
    key = RSA.generate(1024)
    return key

def encrypt(value, key=False):
    """
    Encryption using RSA
    @params value: Value to Encrypt
    @key: The Key used to Encrypt
    @return:Dictionary containing the encrypted data and key
    """
    res = {}
    if not key:
        pub_key = rsa_enc()
        public_key = pub_key.publickey()
        enc_data = public_key.encrypt(str(value), 32)
        res['key'] = base64.encodestring(pub_key.exportKey('DER'))
    else:
        privatekey = RSA.importKey(base64.decodestring(key))
        enc_data = privatekey.encrypt(str(value), 32)
    res['enc_value'] = base64.encodestring(enc_data[0])
    return res

def decrypt(value, key):
    """
    Decryption using RSA
    @params value: Value to Decrypt
    @key: The Key used to Decrypt
    @return:The decrypted data 
    """
    if not key:
        return value
    privatekey = RSA.importKey(base64.decodestring(key))
    return privatekey.decrypt(base64.decodestring(value))
