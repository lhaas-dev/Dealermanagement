import React, { useState, useEffect } from 'react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from './ui/dialog';
import { Label } from './ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Users, Plus, Trash2, Shield, User } from 'lucide-react';
import { toast } from 'sonner';

const UserManagement = ({ token }) => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAddDialog, setShowAddDialog] = useState(false);
  const [formData, setFormData] = useState({
    username: '',
    password: '',
    role: 'user'
  });

  const fetchUsers = async () => {
    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/auth/users`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setUsers(data);
      } else {
        toast.error('Fehler beim Laden der Benutzer');
      }
    } catch (error) {
      console.error('Error fetching users:', error);
      toast.error('Verbindungsfehler');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, [token]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.username || !formData.password) {
      toast.error('Bitte alle Felder ausfüllen');
      return;
    }

    if (formData.password.length < 6) {
      toast.error('Passwort muss mindestens 6 Zeichen haben');
      return;
    }

    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/auth/create-user`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(formData),
      });

      if (response.ok) {
        toast.success('Benutzer erfolgreich erstellt');
        setShowAddDialog(false);
        setFormData({ username: '', password: '', role: 'user' });
        fetchUsers();
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Fehler beim Erstellen des Benutzers');
      }
    } catch (error) {
      console.error('Error creating user:', error);
      toast.error('Verbindungsfehler');
    }
  };

  const deleteUser = async (userId, username) => {
    if (!window.confirm(`Benutzer "${username}" wirklich löschen?`)) return;

    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/auth/users/${userId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        toast.success('Benutzer gelöscht');
        fetchUsers();
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Fehler beim Löschen');
      }
    } catch (error) {
      console.error('Error deleting user:', error);
      toast.error('Verbindungsfehler');
    }
  };

  if (loading) {
    return <div className="text-center py-8">Lade Benutzer...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
            <Users className="w-6 h-6" />
            Benutzerverwaltung
          </h2>
          <p className="text-slate-600">Benutzerkonten verwalten</p>
        </div>

        <Dialog open={showAddDialog} onOpenChange={setShowAddDialog}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="w-4 h-4 mr-2" />
              Benutzer hinzufügen
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Neuen Benutzer erstellen</DialogTitle>
              <DialogDescription>
                Erstellen Sie ein neues Benutzerkonto für das Inventarsystem
              </DialogDescription>
            </DialogHeader>
            <form onSubmit={handleSubmit}>
              <div className="grid gap-4 py-4">
                <div>
                  <Label htmlFor="new-username">Username</Label>
                  <Input
                    id="new-username"
                    required
                    value={formData.username}
                    onChange={(e) => setFormData({...formData, username: e.target.value})}
                    placeholder="Eindeutigen Username eingeben"
                  />
                </div>
                <div>
                  <Label htmlFor="new-password">Passwort</Label>
                  <Input
                    id="new-password"
                    type="password"
                    required
                    minLength={6}
                    value={formData.password}
                    onChange={(e) => setFormData({...formData, password: e.target.value})}
                    placeholder="Mindestens 6 Zeichen"
                  />
                </div>
                <div>
                  <Label htmlFor="new-role">Rolle</Label>
                  <Select value={formData.role} onValueChange={(value) => setFormData({...formData, role: value})}>
                    <SelectTrigger>
                      <SelectValue placeholder="Rolle auswählen" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="user">Benutzer</SelectItem>
                      <SelectItem value="admin">Administrator</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <DialogFooter>
                <Button type="submit">Benutzer erstellen</Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      <div className="grid gap-4">
        {users.map((user) => (
          <Card key={user.id}>
            <CardContent className="flex items-center justify-between p-4">
              <div className="flex items-center gap-4">
                <div className="p-2 bg-blue-100 rounded-full">
                  {user.role === 'admin' ? (
                    <Shield className="w-5 h-5 text-blue-600" />
                  ) : (
                    <User className="w-5 h-5 text-blue-600" />
                  )}
                </div>
                <div>
                  <h3 className="font-semibold">{user.username}</h3>
                  <p className="text-sm text-gray-600">
                    Erstellt: {new Date(user.created_at).toLocaleDateString('de-DE')}
                  </p>
                </div>
              </div>
              
              <div className="flex items-center gap-3">
                <Badge variant={user.role === 'admin' ? 'default' : 'secondary'}>
                  {user.role === 'admin' ? 'Administrator' : 'Benutzer'}
                </Badge>
                
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => deleteUser(user.id, user.username)}
                  className="text-red-600 hover:text-red-700"
                >
                  <Trash2 className="w-4 h-4" />
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {users.length === 0 && (
        <div className="text-center py-12">
          <Users className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-600 mb-2">Keine Benutzer gefunden</h3>
          <p className="text-gray-500 mb-4">Erstellen Sie den ersten Benutzer für das System.</p>
          <Button onClick={() => setShowAddDialog(true)}>
            <Plus className="w-4 h-4 mr-2" />
            Ersten Benutzer erstellen
          </Button>
        </div>
      )}
    </div>
  );
};

export default UserManagement;