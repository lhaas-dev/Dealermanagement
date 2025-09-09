import React, { useState, useEffect, useRef } from "react";
import "./App.css";
import axios from "axios";
import { Toaster } from "./components/ui/sonner";
import { toast } from "sonner";
import { Button } from "./components/ui/button";
import { Input } from "./components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./components/ui/card";
import { Badge } from "./components/ui/badge";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "./components/ui/dialog";
import { Label } from "./components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./components/ui/tabs";
import { Search, Plus, Car, CheckCircle, XCircle, Edit, Trash2, BarChart3, Upload, Camera, FileText, LogOut, Users, Settings } from "lucide-react";
import Login from "./components/Login";
import UserManagement from "./components/UserManagement";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  // Authentication state
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState(null);
  const [authToken, setAuthToken] = useState(null);
  const [currentTab, setCurrentTab] = useState('inventory');

  // Existing state
  const [cars, setCars] = useState([]);
  const [stats, setStats] = useState({});
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [showAddDialog, setShowAddDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [showCSVDialog, setShowCSVDialog] = useState(false);
  const [showPhotoDialog, setShowPhotoDialog] = useState(false);
  const [editingCar, setEditingCar] = useState(null);
  const [markingPresentCar, setMarkingPresentCar] = useState(null);
  const [csvFile, setCsvFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [carPhoto, setCarPhoto] = useState(null);
  const [vinPhoto, setVinPhoto] = useState(null);
  const carPhotoRef = useRef(null);
  const vinPhotoRef = useRef(null);
  const [formData, setFormData] = useState({
    make: "",
    model: "",
    number: "",
    purchase_date: "",
    image_url: "",
    vin: ""
  });

  // Check for existing authentication on component mount
  useEffect(() => {
    const token = localStorage.getItem('auth_token');
    const userData = localStorage.getItem('user_data');
    
    if (token && userData) {
      try {
        const parsedUser = JSON.parse(userData);
        setAuthToken(token);
        setUser(parsedUser);
        setIsAuthenticated(true);
        
        // Set default axios header
        axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      } catch (error) {
        console.error('Error parsing user data:', error);
        handleLogout();
      }
    }
    setLoading(false);
  }, []);

  // Initialize data when authenticated
  useEffect(() => {
    if (isAuthenticated) {
      const loadData = async () => {
        setLoading(true);
        await Promise.all([fetchCars(), fetchStats()]);
        setLoading(false);
      };
      loadData();
    }
  }, [isAuthenticated, searchTerm, statusFilter]);

  // Handle login
  const handleLogin = (loginData) => {
    setAuthToken(loginData.access_token);
    setUser(loginData.user);
    setIsAuthenticated(true);
    
    // Set axios default header
    axios.defaults.headers.common['Authorization'] = `Bearer ${loginData.access_token}`;
  };

  // Handle logout
  const handleLogout = () => {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user_data');
    delete axios.defaults.headers.common['Authorization'];
    setAuthToken(null);
    setUser(null);
    setIsAuthenticated(false);
    setCurrentTab('inventory');
  };

  // Show login screen if not authenticated
  if (!isAuthenticated) {
    return <Login onLogin={handleLogin} />;
  }

  // Fetch cars from API
  const fetchCars = async () => {
    try {
      const params = new URLSearchParams();
      if (searchTerm) params.append('search', searchTerm);
      if (statusFilter && statusFilter !== 'all') params.append('status', statusFilter);
      
      const response = await axios.get(`${API}/cars?${params.toString()}`);
      setCars(response.data);
    } catch (error) {
      console.error('Error fetching cars:', error);
      toast.error('Failed to fetch cars');
    }
  };

  // Fetch inventory stats
  const fetchStats = async () => {
    try {
      const response = await axios.get(`${API}/cars/stats/summary`);
      setStats(response.data);
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  };

  // Handle form submission for adding/editing cars
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    try {
      const carData = {
        ...formData,
        number: formData.number,
        purchase_date: formData.purchase_date || null
      };

      if (editingCar) {
        await axios.put(`${API}/cars/${editingCar.id}`, carData);
        toast.success('Car updated successfully');
        setShowEditDialog(false);
        setEditingCar(null);
      } else {
        await axios.post(`${API}/cars`, carData);
        toast.success('Car added successfully');
        setShowAddDialog(false);
      }

      // Reset form and refresh data
      setFormData({ make: "", model: "", number: "", purchase_date: "", image_url: "", vin: "" });
      await Promise.all([fetchCars(), fetchStats()]);
    } catch (error) {
      console.error('Error saving car:', error);
      toast.error('Failed to save car');
    }
  };

  // Handle CSV upload
  const handleCSVUpload = async () => {
    console.log('CSV Upload started, csvFile:', csvFile);
    
    if (!csvFile) {
      toast.error('Please select a CSV file');
      return;
    }

    // Validate file type
    if (!csvFile.name.toLowerCase().endsWith('.csv')) {
      toast.error('Please select a valid CSV file');
      return;
    }

    // Validate file size (max 5MB)
    if (csvFile.size > 5 * 1024 * 1024) {
      toast.error('File size must be less than 5MB');
      return;
    }

    setUploading(true);
    
    try {
      console.log('Creating FormData...');
      const formData = new FormData();
      formData.append('file', csvFile);

      console.log('Uploading CSV file:', csvFile.name, 'Size:', csvFile.size, 'Type:', csvFile.type);
      console.log('API endpoint:', `${API}/cars/import-csv`);
      
      const response = await axios.post(`${API}/cars/import-csv`, formData, {
        headers: {
          // Let axios set Content-Type automatically for multipart/form-data
        },
        timeout: 30000, // 30 second timeout
      });

      console.log('CSV upload response status:', response.status);
      console.log('CSV upload response data:', response.data);

      const result = response.data;
      
      if (result.success) {
        toast.success(`Successfully imported ${result.imported_count} cars`);
        
        if (result.errors && result.errors.length > 0) {
          console.warn('Import errors:', result.errors);
          toast.warning(`${result.errors.length} rows had errors - check console for details`);
          // Show first few errors in console
          result.errors.forEach((error, index) => {
            if (index < 3) console.error(`Import Error ${index + 1}:`, error);
          });
        }
      } else {
        toast.error('Import failed: ' + (result.message || 'Unknown error'));
      }

      setShowCSVDialog(false);
      setCsvFile(null);
      
      console.log('Refreshing car list and stats...');
      await Promise.all([fetchCars(), fetchStats()]);
      console.log('Refresh completed');
      
    } catch (error) {
      console.error('CSV upload error:', error);
      console.error('Error details:', {
        message: error.message,
        status: error.response?.status,
        statusText: error.response?.statusText,
        data: error.response?.data,
        headers: error.response?.headers
      });
      
      let errorMessage = 'Failed to upload CSV file';
      
      if (error.response?.status === 400) {
        errorMessage = error.response.data?.detail || 'Invalid CSV format or data';
      } else if (error.response?.status === 500) {
        errorMessage = 'Server error processing CSV';
      } else if (error.code === 'ECONNABORTED') {
        errorMessage = 'Upload timeout - file may be too large';
      } else if (error.message) {
        errorMessage += ': ' + error.message;
      }
      
      toast.error(errorMessage);
    } finally {
      setUploading(false);
    }
  };

  // Convert file to base64
  const fileToBase64 = (file) => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.readAsDataURL(file);
      reader.onload = () => resolve(reader.result.split(',')[1]); // Remove data:image/jpeg;base64, prefix
      reader.onerror = error => reject(error);
    });
  };

  // Handle photo capture for car photo
  const handleCarPhotoCapture = async (e) => {
    const file = e.target.files[0];
    if (file) {
      try {
        const base64 = await fileToBase64(file);
        setCarPhoto(base64);
      } catch (error) {
        toast.error('Failed to process car photo');
      }
    }
  };

  // Handle photo capture for VIN photo
  const handleVinPhotoCapture = async (e) => {
    const file = e.target.files[0];
    if (file) {
      try {
        const base64 = await fileToBase64(file);
        setVinPhoto(base64);
      } catch (error) {
        toast.error('Failed to process VIN photo');
      }
    }
  };

  // Handle marking car as present with photos
  const handleMarkPresent = async () => {
    if (!carPhoto || !vinPhoto) {
      toast.error('Both car photo and VIN photo are required');
      return;
    }

    try {
      await axios.patch(`${API}/cars/${markingPresentCar.id}/status`, {
        status: 'present',
        car_photo: carPhoto,
        vin_photo: vinPhoto
      });
      
      toast.success('Car marked as present with photo verification');
      setShowPhotoDialog(false);
      setMarkingPresentCar(null);
      setCarPhoto(null);
      setVinPhoto(null);
      await Promise.all([fetchCars(), fetchStats()]);
    } catch (error) {
      console.error('Error updating status:', error);
      toast.error('Failed to update car status');
    }
  };

  // Handle status toggle - simplified for marking absent, opens photo dialog for present
  const toggleCarStatus = async (car) => {
    if (car.status === 'present') {
      // Mark as absent (no photos needed)
      try {
        await axios.patch(`${API}/cars/${car.id}/status`, { status: 'absent' });
        toast.success('Car marked as absent');
        await Promise.all([fetchCars(), fetchStats()]);
      } catch (error) {
        console.error('Error updating status:', error);
        toast.error('Failed to update status');
      }
    } else {
      // Mark as present (requires photos)
      setMarkingPresentCar(car);
      setShowPhotoDialog(true);
      setCarPhoto(null);
      setVinPhoto(null);
    }
  };

  // Handle car deletion (admin only)
  const deleteCar = async (carId) => {
    if (!window.confirm('Möchten Sie dieses Fahrzeug wirklich löschen?')) return;
    
    try {
      await axios.delete(`${API}/cars/${carId}`);
      toast.success('Fahrzeug erfolgreich gelöscht');
      await Promise.all([fetchCars(), fetchStats()]);
    } catch (error) {
      console.error('Error deleting car:', error);
      toast.error('Fehler beim Löschen: ' + (error.response?.data?.detail || error.message));
    }
  };

  // Handle delete all cars (admin only)
  const deleteAllCars = async () => {
    const confirmed = window.confirm(
      '⚠️ ACHTUNG: Möchten Sie wirklich ALLE Fahrzeuge löschen?\n\nDiese Aktion kann nicht rückgängig gemacht werden!'
    );
    
    if (!confirmed) return;
    
    const confirmation = prompt('Zur Bestätigung tippen Sie: ALLE LÖSCHEN');
    if (confirmation !== 'ALLE LÖSCHEN') {
      toast.error('Löschung abgebrochen - falsche Bestätigung');
      return;
    }

    try {
      const response = await axios.delete(`${API}/cars`);
      const result = response.data;
      toast.success(`Alle ${result.deleted_count} Fahrzeuge wurden gelöscht`);
      await Promise.all([fetchCars(), fetchStats()]);
    } catch (error) {
      console.error('Error deleting all cars:', error);
      toast.error('Fehler beim Löschen aller Fahrzeuge: ' + (error.response?.data?.detail || error.message));
    }
  };

  // Open edit dialog
  const openEditDialog = (car) => {
    setEditingCar(car);
    setFormData({
      make: car.make,
      model: car.model,
      number: car.number,
      purchase_date: car.purchase_date || "",
      image_url: car.image_url || "",
      vin: car.vin || ""
    });
    setShowEditDialog(true);
  };

  const resetForm = () => {
    setFormData({ make: "", model: "", number: "", purchase_date: "", image_url: "", vin: "" });
    setEditingCar(null);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      <div className="container mx-auto px-4 py-8">
        {/* Header with User Info */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-4xl font-bold text-slate-800 mb-2 flex items-center gap-3">
              <Car className="w-10 h-10 text-blue-600" />
              Dealership Inventory
            </h1>
            <p className="text-slate-600">Fahrzeug-Inventarsystem mit Foto-Verifizierung</p>
          </div>
          
          <div className="flex items-center gap-4">
            <div className="text-right">
              <p className="font-semibold text-slate-800">{user.username}</p>
              <p className="text-sm text-slate-600">
                {user.role === 'admin' ? 'Administrator' : 'Benutzer'}
              </p>
            </div>
            <Button variant="outline" onClick={handleLogout}>
              <LogOut className="w-4 h-4 mr-2" />
              Abmelden
            </Button>
          </div>
        </div>

        {/* Navigation Tabs */}
        <Tabs value={currentTab} onValueChange={setCurrentTab} className="w-full">
          <TabsList className="grid w-full grid-cols-2 mb-8">
            <TabsTrigger value="inventory" className="flex items-center gap-2">
              <Car className="w-4 h-4" />
              Inventar
            </TabsTrigger>
            {user.role === 'admin' && (
              <TabsTrigger value="users" className="flex items-center gap-2">
                <Users className="w-4 h-4" />
                Benutzerverwaltung
              </TabsTrigger>
            )}
          </TabsList>

          {/* Inventory Tab */}
          <TabsContent value="inventory">
            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Gesamt Fahrzeuge</CardTitle>
                  <BarChart3 className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{stats.total_cars || 0}</div>
                </CardContent>
              </Card>
              
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Anwesend</CardTitle>
                  <CheckCircle className="h-4 w-4 text-green-600" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-green-600">{stats.present_cars || 0}</div>
                </CardContent>
              </Card>
              
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Abwesend</CardTitle>
                  <XCircle className="h-4 w-4 text-red-600" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-red-600">{stats.absent_cars || 0}</div>
                </CardContent>
              </Card>
              
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Anwesend %</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{stats.present_percentage || 0}%</div>
                </CardContent>
              </Card>
            </div>

            {/* Rest of the existing inventory interface */}
            {/* Controls */}
            <div className="flex flex-col sm:flex-row gap-4 mb-6">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                <Input
                  placeholder="Suche nach Marke, Modell oder VIN..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
              
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="w-full sm:w-[180px]">
                  <SelectValue placeholder="Nach Status filtern" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Alle Status</SelectItem>
                  <SelectItem value="present">Anwesend</SelectItem>
                  <SelectItem value="absent">Abwesend</SelectItem>
                </SelectContent>
              </Select>

              {/* CSV Upload Dialog */}
              <Dialog open={showCSVDialog} onOpenChange={setShowCSVDialog}>
                <DialogTrigger asChild>
                  <Button variant="outline">
                    <Upload className="w-4 h-4 mr-2" />
                    CSV Import
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>CSV-Datei mit Spalten importieren</DialogTitle>
                    <DialogDescription>
                      CSV-Datei mit Spalten: make, model, number, purchase_date (optional), vin (optional), image_url (optional)
                      <br />Alle importierten Fahrzeuge werden als "abwesend" markiert.
                    </DialogDescription>
                  </DialogHeader>
                  <div className="py-4">
                    <Label htmlFor="csv-file">CSV-Datei auswählen</Label>
                    <Input
                      id="csv-file"
                      type="file"
                      accept=".csv"
                      onChange={(e) => setCsvFile(e.target.files[0])}
                      className="mt-2"
                    />
                    {csvFile && (
                      <p className="text-sm text-gray-600 mt-2">
                        Ausgewählt: {csvFile.name}
                      </p>
                    )}
                  </div>
                  <DialogFooter>
                    <Button onClick={handleCSVUpload} disabled={!csvFile || uploading}>
                      {uploading ? 'Wird hochgeladen...' : 'Fahrzeuge importieren'}
                    </Button>
                  </DialogFooter>
                </DialogContent>
              </Dialog>

              <Dialog open={showAddDialog} onOpenChange={setShowAddDialog}>
                <DialogTrigger asChild>
                  <Button onClick={resetForm}>
                    <Plus className="w-4 h-4 mr-2" />
                    Fahrzeug hinzufügen
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>Neues Fahrzeug hinzufügen</DialogTitle>
                    <DialogDescription>Neues Fahrzeug zum Inventar hinzufügen (wird als abwesend markiert)</DialogDescription>
                  </DialogHeader>
                  <form onSubmit={handleSubmit}>
                    <div className="grid gap-4 py-4">
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <Label htmlFor="make">Marke</Label>
                          <Input
                            id="make"
                            required
                            value={formData.make}
                            onChange={(e) => setFormData({...formData, make: e.target.value})}
                          />
                        </div>
                        <div>
                          <Label htmlFor="model">Modell</Label>
                          <Input
                            id="model"
                            required
                            value={formData.model}
                            onChange={(e) => setFormData({...formData, model: e.target.value})}
                          />
                        </div>
                      </div>
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <Label htmlFor="number">Nummer</Label>
                          <Input
                            id="number"
                            required
                            value={formData.number}
                            onChange={(e) => setFormData({...formData, number: e.target.value})}
                          />
                        </div>
                        <div>
                          <Label htmlFor="purchase_date">Einkaufsdatum</Label>
                          <Input
                            id="purchase_date"
                            type="date"
                            value={formData.purchase_date}
                            onChange={(e) => setFormData({...formData, purchase_date: e.target.value})}
                          />
                        </div>
                      </div>
                      <div>
                        <Label htmlFor="vin">VIN</Label>
                        <Input
                          id="vin"
                          value={formData.vin}
                          onChange={(e) => setFormData({...formData, vin: e.target.value})}
                        />
                      </div>
                      <div>
                        <Label htmlFor="image_url">Bild-URL</Label>
                        <Input
                          id="image_url"
                          type="url"
                          value={formData.image_url}
                          onChange={(e) => setFormData({...formData, image_url: e.target.value})}
                        />
                      </div>
                    </div>
                    <DialogFooter>
                      <Button type="submit">Fahrzeug hinzufügen</Button>
                    </DialogFooter>
                  </form>
                </DialogContent>
              </Dialog>

              {/* Delete All Button (Admin only) */}
              {user.role === 'admin' && cars.length > 0 && (
                <Button 
                  variant="destructive" 
                  onClick={deleteAllCars}
                  className="flex items-center gap-2"
                >
                  <Trash2 className="w-4 h-4" />
                  Alle löschen
                </Button>
              )}
            </div>

            {/* Rest of the cars grid and dialogs - keeping existing code */}
            {/* Cars Grid */}
            {loading ? (
              <div className="text-center py-8">Wird geladen...</div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {cars.map((car) => {
                  // Use verification photo if car is present and has car_photo, otherwise use image_url
                  const displayImage = car.status === 'present' && car.car_photo 
                    ? `data:image/jpeg;base64,${car.car_photo}` 
                    : car.image_url;
                  
                  const isVerificationPhoto = car.status === 'present' && car.car_photo;
                  
                  return (
                    <Card key={car.id} className="overflow-hidden hover:shadow-lg transition-shadow">
                      {displayImage && (
                        <div className="h-48 bg-gray-200 overflow-hidden relative">
                          <img
                            src={displayImage}
                            alt={`${car.make} ${car.model}`}
                            className="w-full h-full object-cover"
                            onError={(e) => {
                              e.target.style.display = 'none';
                            }}
                          />
                          {isVerificationPhoto && (
                            <div className="absolute top-2 left-2 bg-green-600 text-white px-2 py-1 rounded-full text-xs flex items-center gap-1">
                              <Camera className="w-3 h-3" />
                              Verified
                            </div>
                          )}
                          {car.status === 'present' && car.vin_photo && (
                            <button
                              onClick={() => {
                                // Show VIN photo in a modal or new tab
                                const vinImage = `data:image/jpeg;base64,${car.vin_photo}`;
                                const newWindow = window.open();
                                newWindow.document.write(`
                                  <html>
                                    <head><title>VIN Verification - ${car.make} ${car.model}</title></head>
                                    <body style="margin:0; display:flex; justify-content:center; align-items:center; min-height:100vh; background:#000;">
                                      <img src="${vinImage}" style="max-width:100%; max-height:100%; object-fit:contain;" alt="VIN Verification Photo" />
                                    </body>
                                  </html>
                                `);
                              }}
                              className="absolute top-2 right-2 bg-blue-600 text-white p-1 rounded-full hover:bg-blue-700 transition-colors"
                              title="VIN-Foto anzeigen"
                            >
                              <FileText className="w-3 h-3" />
                            </button>
                          )}
                        </div>
                      )}
                      <CardHeader>
                        <div className="flex justify-between items-start">
                          <div>
                            <CardTitle className="text-lg">{car.make} {car.model}</CardTitle>
                            <CardDescription>Nr. {car.number}</CardDescription>
                          </div>
                          <Badge variant={car.status === 'present' ? 'default' : 'destructive'}>
                            {car.status === 'present' ? 'Anwesend' : 'Abwesend'}
                            {car.status === 'present' && car.car_photo && (
                              <Camera className="w-3 h-3 ml-1" title="Foto verifiziert" />
                            )}
                          </Badge>
                        </div>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-2">
                          {car.purchase_date && (
                            <p className="text-lg font-semibold text-blue-600">
                              Eingekauft: {new Date(car.purchase_date).toLocaleDateString('de-DE')}
                            </p>
                          )}
                          {car.vin && (
                            <p className="text-sm text-gray-600">VIN: {car.vin}</p>
                          )}
                          <div className="flex gap-2 pt-4">
                            <Button
                              size="sm"
                              variant={car.status === 'present' ? 'destructive' : 'default'}
                              onClick={() => toggleCarStatus(car)}
                              className="flex-1"
                            >
                              {car.status === 'present' ? (
                                <>
                                  <XCircle className="w-4 h-4 mr-1" />
                                  Als abwesend markieren
                                </>
                              ) : (
                                <>
                                  <CheckCircle className="w-4 h-4 mr-1" />
                                  Als anwesend markieren
                                </>
                              )}
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => openEditDialog(car)}
                            >
                              <Edit className="w-4 h-4" />
                            </Button>
                            {/* Delete button only for admins */}
                            {user.role === 'admin' && (
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => deleteCar(car.id)}
                                className="text-red-600 hover:text-red-700"
                              >
                                <Trash2 className="w-4 h-4" />
                              </Button>
                            )}
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
            )}

            {/* Photo Verification Dialog */}
            <Dialog open={showPhotoDialog} onOpenChange={setShowPhotoDialog}>
              <DialogContent className="max-w-md">
                <DialogHeader>
                  <DialogTitle>Foto-Verifizierung erforderlich</DialogTitle>
                  <DialogDescription>
                    Um dieses Fahrzeug als anwesend zu markieren, nehmen Sie bitte Fotos vom Fahrzeug und der VIN-Plakette auf
                  </DialogDescription>
                </DialogHeader>
                <div className="space-y-4 py-4">
                  {/* Car Photo */}
                  <div>
                    <Label>Fahrzeug-Foto</Label>
                    <div className="mt-2 space-y-2">
                      <Button
                        variant="outline"
                        onClick={() => carPhotoRef.current?.click()}
                        className="w-full"
                      >
                        <Camera className="w-4 h-4 mr-2" />
                        {carPhoto ? 'Fahrzeug-Foto aufgenommen ✓' : 'Fahrzeug-Foto aufnehmen'}
                      </Button>
                      <input
                        ref={carPhotoRef}
                        type="file"
                        accept="image/*"
                        capture="environment"
                        onChange={handleCarPhotoCapture}
                        className="hidden"
                      />
                      {carPhoto && (
                        <div className="w-full h-32 bg-green-50 border-2 border-green-200 rounded flex items-center justify-center">
                          <CheckCircle className="w-8 h-8 text-green-600" />
                          <span className="ml-2 text-green-700">Fahrzeug-Foto aufgenommen</span>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* VIN Photo */}
                  <div>
                    <Label>VIN-Foto</Label>
                    <div className="mt-2 space-y-2">
                      <Button
                        variant="outline"
                        onClick={() => vinPhotoRef.current?.click()}
                        className="w-full"
                      >
                        <FileText className="w-4 h-4 mr-2" />
                        {vinPhoto ? 'VIN-Foto aufgenommen ✓' : 'VIN-Foto aufnehmen'}
                      </Button>
                      <input
                        ref={vinPhotoRef}
                        type="file"
                        accept="image/*"
                        capture="environment"
                        onChange={handleVinPhotoCapture}
                        className="hidden"
                      />
                      {vinPhoto && (
                        <div className="w-full h-32 bg-green-50 border-2 border-green-200 rounded flex items-center justify-center">
                          <CheckCircle className="w-8 h-8 text-green-600" />
                          <span className="ml-2 text-green-700">VIN-Foto aufgenommen</span>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
                <DialogFooter>
                  <Button
                    onClick={handleMarkPresent}
                    disabled={!carPhoto || !vinPhoto}
                    className="w-full"
                  >
                    Als anwesend markieren
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>

            {/* Edit Dialog */}
            <Dialog open={showEditDialog} onOpenChange={setShowEditDialog}>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Fahrzeug bearbeiten</DialogTitle>
                  <DialogDescription>Fahrzeug-Informationen aktualisieren</DialogDescription>
                </DialogHeader>
                <form onSubmit={handleSubmit}>
                  <div className="grid gap-4 py-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label htmlFor="edit-make">Marke</Label>
                        <Input
                          id="edit-make"
                          required
                          value={formData.make}
                          onChange={(e) => setFormData({...formData, make: e.target.value})}
                        />
                      </div>
                      <div>
                        <Label htmlFor="edit-model">Modell</Label>
                        <Input
                          id="edit-model"
                          required
                          value={formData.model}
                          onChange={(e) => setFormData({...formData, model: e.target.value})}
                        />
                      </div>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label htmlFor="edit-number">Nummer</Label>
                        <Input
                          id="edit-number"
                          required
                          value={formData.number}
                          onChange={(e) => setFormData({...formData, number: e.target.value})}
                        />
                      </div>
                      <div>
                        <Label htmlFor="edit-purchase_date">Einkaufsdatum</Label>
                        <Input
                          id="edit-purchase_date"
                          type="date"
                          value={formData.purchase_date}
                          onChange={(e) => setFormData({...formData, purchase_date: e.target.value})}
                        />
                      </div>
                    </div>
                    <div>
                      <Label htmlFor="edit-vin">VIN</Label>
                      <Input
                        id="edit-vin"
                        value={formData.vin}
                        onChange={(e) => setFormData({...formData, vin: e.target.value})}
                      />
                    </div>
                    <div>
                      <Label htmlFor="edit-image_url">Bild-URL</Label>
                      <Input
                        id="edit-image_url"
                        type="url"
                        value={formData.image_url}
                        onChange={(e) => setFormData({...formData, image_url: e.target.value})}
                      />
                    </div>
                  </div>
                  <DialogFooter>
                    <Button type="submit">Fahrzeug aktualisieren</Button>
                  </DialogFooter>
                </form>
              </DialogContent>
            </Dialog>

            {cars.length === 0 && !loading && (
              <div className="text-center py-12">
                <Car className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-gray-600 mb-2">Keine Fahrzeuge gefunden</h3>
                <p className="text-gray-500 mb-4">Beginnen Sie, indem Sie Fahrzeuge einzeln hinzufügen oder aus CSV importieren.</p>
                <div className="flex justify-center gap-4">
                  <Button onClick={() => setShowAddDialog(true)}>
                    <Plus className="w-4 h-4 mr-2" />
                    Erstes Fahrzeug hinzufügen
                  </Button>
                  <Button variant="outline" onClick={() => setShowCSVDialog(true)}>
                    <Upload className="w-4 h-4 mr-2" />
                    CSV importieren
                  </Button>
                </div>
              </div>
            )}
          </TabsContent>

          {/* User Management Tab (Admin only) */}
          {user.role === 'admin' && (
            <TabsContent value="users">
              <UserManagement token={authToken} />
            </TabsContent>
          )}
        </Tabs>
      </div>
      
      <Toaster />
    </div>
  );
}

export default App;